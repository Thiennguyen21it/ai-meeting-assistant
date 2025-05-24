from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from app.api.deps import SessionDep, get_db, CurrentUser
from app.models import (
    Meeting, MeetingCreate, MeetingUpdate, MeetingStatus, 
    MeetingPublic, MeetingsPublic, Message
)

router = APIRouter()

@router.post("/", response_model=MeetingPublic)
def create_meeting(
    db: SessionDep,
    meeting_in: MeetingCreate,
    current_user: CurrentUser,
) -> MeetingPublic:
    """
    Create new meeting
    """
    # Create new meeting
    new_meeting = Meeting(
        title=meeting_in.title,
        description=meeting_in.description,
        start_time=datetime.utcnow() if not meeting_in.start_time else meeting_in.start_time,
        status=MeetingStatus.SCHEDULED,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)
    
    return MeetingPublic(
        id=new_meeting.id,
        title=new_meeting.title,
        description=new_meeting.description,
        start_time=new_meeting.start_time,
        end_time=new_meeting.end_time,
        status=new_meeting.status,
        owner_id=new_meeting.owner_id,
        created_at=new_meeting.created_at,
        updated_at=new_meeting.updated_at
    )

@router.get("/", response_model=MeetingsPublic)
def list_meetings(
    db: SessionDep, 
    current_user: CurrentUser, 
    skip: int = 0, 
    limit: int = 100
) -> MeetingsPublic:
    """
    List user meetings
    """
    # If superuser, get all meetings, otherwise get only user's meetings
    if current_user.is_superuser:
        meetings = db.exec(select(Meeting).offset(skip).limit(limit)).all()
        count_query = db.exec(select(Meeting)).all()
    else:
        meetings = db.exec(
            select(Meeting)
            .where(Meeting.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        ).all()
        count_query = db.exec(
            select(Meeting).where(Meeting.owner_id == current_user.id)
        ).all()
    
    # Convert to public format
    meetings_public = [
        MeetingPublic(
            id=meeting.id,
            title=meeting.title,
            description=meeting.description,
            start_time=meeting.start_time,
            end_time=meeting.end_time,
            status=meeting.status,
            owner_id=meeting.owner_id,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at
        )
        for meeting in meetings
    ]
    
    return MeetingsPublic(data=meetings_public, count=len(count_query))

@router.get("/{meeting_id}", response_model=MeetingPublic)
def get_meeting(
    db: SessionDep, 
    meeting_id: UUID, 
    current_user: CurrentUser
) -> MeetingPublic:
    """
    Get meeting details
    """
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check ownership or superuser status
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return MeetingPublic(
        id=meeting.id,
        title=meeting.title,
        description=meeting.description,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        status=meeting.status,
        owner_id=meeting.owner_id,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at
    )

@router.put("/{meeting_id}", response_model=MeetingPublic)
def update_meeting(
    db: SessionDep, 
    meeting_id: UUID, 
    meeting_in: MeetingUpdate, 
    current_user: CurrentUser
) -> MeetingPublic:
    """
    Update meeting
    """
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check ownership
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update meeting fields
    update_data = meeting_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting, field, value)
    
    meeting.updated_at = datetime.utcnow()
    
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    
    return MeetingPublic(
        id=meeting.id,
        title=meeting.title,
        description=meeting.description,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        status=meeting.status,
        owner_id=meeting.owner_id,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at
    )

@router.delete("/{meeting_id}", response_model=Message)
def delete_meeting(
    db: SessionDep, 
    meeting_id: UUID, 
    current_user: CurrentUser
) -> Message:
    """
    Delete meeting
    """
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check ownership
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(meeting)
    db.commit()
    return Message(message="Meeting deleted successfully")

# Additional meeting management endpoints
@router.post("/{meeting_id}/start", response_model=MeetingPublic)
def start_meeting(
    db: SessionDep, 
    meeting_id: UUID, 
    current_user: CurrentUser
) -> MeetingPublic:
    """
    Start a meeting
    """
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check ownership
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    meeting.status = MeetingStatus.ONGOING
    meeting.start_time = datetime.utcnow()
    meeting.updated_at = datetime.utcnow()
    
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    
    return MeetingPublic(
        id=meeting.id,
        title=meeting.title,
        description=meeting.description,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        status=meeting.status,
        owner_id=meeting.owner_id,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at
    )

@router.post("/{meeting_id}/end", response_model=MeetingPublic)
def end_meeting(
    db: SessionDep, 
    meeting_id: UUID, 
    current_user: CurrentUser
) -> MeetingPublic:
    """
    End a meeting
    """
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check ownership
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    meeting.status = MeetingStatus.ENDED
    meeting.end_time = datetime.utcnow()
    meeting.updated_at = datetime.utcnow()
    
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    
    return MeetingPublic(
        id=meeting.id,
        title=meeting.title,
        description=meeting.description,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        status=meeting.status,
        owner_id=meeting.owner_id,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at
    ) 