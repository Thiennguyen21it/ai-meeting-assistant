from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlmodel import Session, select
from datetime import datetime

from app.api.deps import SessionDep, CurrentUser
from app.models import (
    Meeting, Recording, Transcript, TranscriptCreate, TranscriptPublic, 
    TranscriptsPublic, Message
)
from app.services.action_items_service import search_meeting_content

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time transcription"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, meeting_id: str):
        await websocket.accept()
        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = []
        self.active_connections[meeting_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, meeting_id: str):
        if meeting_id in self.active_connections:
            self.active_connections[meeting_id].remove(websocket)
            if not self.active_connections[meeting_id]:
                del self.active_connections[meeting_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_meeting(self, message: str, meeting_id: str):
        if meeting_id in self.active_connections:
            for connection in self.active_connections[meeting_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove broken connections
                    pass


manager = ConnectionManager()


@router.get("/{meeting_id}/transcriptions", response_model=TranscriptsPublic)
async def get_meeting_transcriptions(
    meeting_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
) -> TranscriptsPublic:
    """
    Get transcriptions for a specific meeting
    """
    # Verify meeting exists and user has access
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get recordings for this meeting
    recordings = session.exec(
        select(Recording).where(Recording.meeting_id == meeting_id)
    ).all()
    
    # Get transcripts for all recordings
    transcript_list = []
    for recording in recordings:
        transcripts = session.exec(
            select(Transcript)
            .where(Transcript.recording_id == recording.id)
            .offset(skip)
            .limit(limit)
        ).all()
        transcript_list.extend(transcripts)
    
    # Convert to public format
    transcripts_public = [
        TranscriptPublic(
            id=transcript.id,
            recording_id=transcript.recording_id,
            content=transcript.content,
            created_at=transcript.created_at
        )
        for transcript in transcript_list
    ]
    
    return TranscriptsPublic(data=transcripts_public, count=len(transcripts_public))


@router.post("/{meeting_id}/transcriptions", response_model=TranscriptPublic)
async def add_meeting_transcription(
    meeting_id: UUID,
    transcript_data: TranscriptCreate,
    session: SessionDep,
    current_user: CurrentUser
) -> TranscriptPublic:
    """
    Add a new transcription to a meeting
    """
    # Verify meeting exists and user has access
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify recording exists
    recording = session.get(Recording, transcript_data.recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    if recording.meeting_id != meeting_id:
        raise HTTPException(status_code=400, detail="Recording does not belong to this meeting")
    
    # Create new transcript
    transcript = Transcript(
        content=transcript_data.content,
        recording_id=transcript_data.recording_id,
        created_at=datetime.now()
    )
    
    session.add(transcript)
    session.commit()
    session.refresh(transcript)
    
    # Broadcast to WebSocket connections
    await manager.broadcast_to_meeting(
        f"New transcription: {transcript_data.content}",
        str(meeting_id)
    )
    
    return TranscriptPublic(
        id=transcript.id,
        recording_id=transcript.recording_id,
        content=transcript.content,
        created_at=transcript.created_at
    )


@router.websocket("/ws/meetings/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
    """
    WebSocket endpoint for real-time transcription
    """
    await manager.connect(websocket, meeting_id)
    try:
        while True:
            # Receive audio data or transcription commands
            data = await websocket.receive_text()
            
            # Echo back for now (in real implementation, this would process audio)
            await manager.send_personal_message(f"Received: {data}", websocket)
            
            # In a real implementation, you would:
            # 1. Process audio data
            # 2. Convert speech to text
            # 3. Store transcription in database
            # 4. Broadcast to all connected clients
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id)


@router.get("/{meeting_id}/search")
async def search_meeting_content_endpoint(
    meeting_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    q: str = Query(..., description="Search query")
) -> Dict[str, Any]:
    """
    Search through meeting content
    """
    # Verify meeting exists and user has access
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get all transcriptions for this meeting
    recordings = session.exec(
        select(Recording).where(Recording.meeting_id == meeting_id)
    ).all()
    
    all_transcript_text = ""
    for recording in recordings:
        transcripts = session.exec(
            select(Transcript).where(Transcript.recording_id == recording.id)
        ).all()
        for transcript in transcripts:
            all_transcript_text += transcript.content + "\n"
    
    if not all_transcript_text.strip():
        return {
            "query": q,
            "meeting_id": str(meeting_id),
            "relevance_score": 0,
            "excerpts": [],
            "summary": "No transcriptions available for this meeting",
            "total_matches": 0
        }
    
    # Use AI service to search content
    search_results = await search_meeting_content(q, all_transcript_text)
    
    # Add query and meeting info to results
    search_results["query"] = q
    search_results["meeting_id"] = str(meeting_id)
    
    return search_results 