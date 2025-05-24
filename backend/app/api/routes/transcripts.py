from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    User, Meeting, Recording, Transcript, TranscriptCreate, 
    TranscriptPublic, TranscriptsPublic
)

router = APIRouter()


@router.post("/{recording_id}", response_model=TranscriptPublic)
def create_transcript(
    db: SessionDep,
    recording_id: UUID,
    transcript_in: TranscriptCreate,
    current_user: CurrentUser,
) -> TranscriptPublic:
    """
    Create a transcript for a recording.
    """
    # Check if recording exists
    recording = db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )
    
    # Check if user has access to the meeting
    meeting = db.get(Meeting, recording.meeting_id)
    if not meeting or meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Create transcript
    transcript = Transcript(
        recording_id=recording_id,
        content=transcript_in.content,
    )
    
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    return TranscriptPublic(
        id=transcript.id,
        recording_id=transcript.recording_id,
        content=transcript.content,
        created_at=transcript.created_at,
    )


@router.get("/{recording_id}", response_model=TranscriptsPublic)
def read_transcripts(
    db: SessionDep,
    recording_id: UUID,
    current_user: CurrentUser,
) -> TranscriptsPublic:
    """
    Get all transcripts for a recording.
    """
    # Check if recording exists
    recording = db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )
    
    # Check if user has access to the meeting
    meeting = db.get(Meeting, recording.meeting_id)
    if not meeting or meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get transcripts
    transcripts_query = select(Transcript).where(Transcript.recording_id == recording_id)
    transcripts = db.exec(transcripts_query).all()
    count = len(transcripts)
    
    transcripts_public = [
        TranscriptPublic(
            id=transcript.id,
            recording_id=transcript.recording_id,
            content=transcript.content,
            created_at=transcript.created_at,
        )
        for transcript in transcripts
    ]
    
    return TranscriptsPublic(data=transcripts_public, count=count) 