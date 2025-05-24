from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select
from datetime import datetime
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Transcript, User, Meeting, Recording, RecordingCreate, RecordingUpdate, 
    RecordingPublic, RecordingsPublic, RecordingStatus
)
import os
import uuid
from pathlib import Path
import asyncio
import httpx
from app.core.config import settings
from app.services.transcription import transcribe_audio
from app.core.db import engine

router = APIRouter()

@router.post("/start", response_model=RecordingPublic)
def start_recording(
     db: SessionDep,
    recording_in: RecordingCreate,
    current_user: CurrentUser,
) -> RecordingPublic:
    """
    Start a new recording for a meeting.
    """
    # Check if meeting exists and user has access
    meeting = db.get(Meeting, recording_in.meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    
    if meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this meeting",
        )
    
    # Create new recording
    recording = Recording(
        meeting_id=recording_in.meeting_id,
        start_time=recording_in.start_time,
        status=RecordingStatus.RECORDING,
    )
    
    db.add(recording)
    db.commit()
    db.refresh(recording)
    
    return RecordingPublic(
        id=recording.id,
        meeting_id=recording.meeting_id,
        start_time=recording.start_time,
        end_time=recording.end_time,
        status=recording.status,
        file_url=recording.file_url,
        transcript_url=recording.transcript_url,
        created_at=recording.created_at,
        updated_at=recording.updated_at,
    )

@router.post("/end/{recording_id}", response_model=RecordingPublic)
async def end_recording(
    db: SessionDep,
    recording_id: UUID,
    current_user: CurrentUser,
    audio_file: UploadFile = File(...),
) -> RecordingPublic:
    """
    End an ongoing recording and upload the audio file.
    """
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
    
    # Create directory for storing files if it doesn't exist
    upload_dir = Path("data/recordings")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a unique filename for the audio file
    file_extension = os.path.splitext(audio_file.filename)[1]
    unique_filename = f"{recording_id}{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        contents = await audio_file.read()
        buffer.write(contents)
    
    # Update recording status and file information
    recording.status = RecordingStatus.COMPLETED
    recording.end_time = datetime.now()
    recording.updated_at = datetime.now()
    recording.file_url = f"/recordings/{unique_filename}"
    
    db.add(recording)
    db.commit()
    db.refresh(recording)
    
    # Start transcription process in the background
    # We'll use asyncio.create_task to run this in the background
    asyncio.create_task(
        process_transcription(db, recording.id, str(file_path))
    )
    
    return RecordingPublic(
        id=recording.id,
        meeting_id=recording.meeting_id,
        start_time=recording.start_time,
        end_time=recording.end_time,
        status=recording.status,
        file_url=recording.file_url,
        transcript_url=recording.transcript_url,
        created_at=recording.created_at,
        updated_at=recording.updated_at,
    )

async def process_transcription(db: Session, recording_id: UUID, file_path: str):
    """
    Process the audio file for transcription.
    This runs as a background task after the recording is ended.
    """
    try:
        # Create a new session for this background task
        with Session(engine) as session:
            recording = session.get(Recording, recording_id)
            if not recording:
                print(f"Recording {recording_id} not found for transcription")
                return
            
            # Call the transcription service
            transcript_text = await transcribe_audio(file_path)
            
            if not transcript_text:
                print(f"Failed to transcribe recording {recording_id}")
                return
            
            # Create a new transcript record
            transcript = Transcript(
                content=transcript_text,
                recording_id=recording_id,
                created_at=datetime.now()
            )
            
            session.add(transcript)
            
            # Update the recording with the transcript URL
            transcript_filename = f"{recording_id}_transcript.txt"
            transcript_path = Path("data/transcripts")
            transcript_path.mkdir(parents=True, exist_ok=True)
            
            # Save transcript to file
            with open(transcript_path / transcript_filename, "w") as f:
                f.write(transcript_text)
            
            recording.transcript_url = f"/transcripts/{transcript_filename}"
            recording.updated_at = datetime.now()
            
            session.add(recording)
            session.commit()
            
            print(f"Transcription completed for recording {recording_id}")
    except Exception as e:
        print(f"Error processing transcription for recording {recording_id}: {str(e)}")

@router.get("/", response_model=RecordingsPublic)
def read_recordings(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> RecordingsPublic:
    """
    Retrieve recordings for meetings owned by the current user.
    """
    # Get meetings owned by the user
    meetings_query = select(Meeting.id).where(Meeting.owner_id == str(current_user.id))
    print(current_user.id)
    print(meetings_query)
    meeting_ids = [row.id for row in db.exec(meetings_query)]
    
    # Get recordings for those meetings
    recordings_query = select(Recording).where(
        Recording.meeting_id.in_(meeting_ids)
    ).offset(skip).limit(limit)
    
    recordings = db.exec(recordings_query).all()
    count = len(recordings)
    
    recordings_public = [
        RecordingPublic(
            id=recording.id,
            meeting_id=recording.meeting_id,
            start_time=recording.start_time,
            end_time=recording.end_time,
            status=recording.status,
            file_url=recording.file_url,
            transcript_url=recording.transcript_url,
            created_at=recording.created_at,
            updated_at=recording.updated_at,
        )
        for recording in recordings
    ]
    
    return RecordingsPublic(data=recordings_public, count=count)

@router.get("/{recording_id}", response_model=RecordingPublic)
def read_recording(
    db: SessionDep,
    recording_id: UUID,
    current_user: CurrentUser,
) -> RecordingPublic:
    """
    Get a specific recording by ID.
    """
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
    
    return RecordingPublic(
        id=recording.id,
        meeting_id=recording.meeting_id,
        start_time=recording.start_time,
        end_time=recording.end_time,
        status=recording.status,
        file_url=recording.file_url,
        transcript_url=recording.transcript_url,
        created_at=recording.created_at,
        updated_at=recording.updated_at,
    ) 