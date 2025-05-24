from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from app.api.deps import SessionDep, get_db, CurrentUser
from app.models import Meeting, MeetingCreate, MeetingUpdate, MeetingStatus

router = APIRouter()

@router.post("/", response_model=Meeting)
def create_meeting(
    db: SessionDep,
    meeting_in: MeetingCreate,
    current_user: CurrentUser,
) -> Meeting:
    # Create new meeting
    new_meeting = Meeting(
        title=meeting_in.title,
        start_time=datetime.utcnow() if not meeting_in.start_time else meeting_in.start_time,
        status=MeetingStatus.SCHEDULED,
        owner_id=current_user.id
    )
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)
    return new_meeting

@router.put("/{meeting_id}", response_model=Meeting)
def update_meeting(db: SessionDep, meeting_id: UUID, meeting_in: MeetingUpdate, current_user: CurrentUser):
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
    
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting

@router.post("/{meeting_id}/start", response_model=Meeting)
def start_meeting(db: SessionDep, meeting_id: UUID, current_user: CurrentUser):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check ownership
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    meeting.status = MeetingStatus.ONGOING
    meeting.start_time = datetime.utcnow()
    
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting

@router.post("/{meeting_id}/end", response_model=Meeting)
def end_meeting(db: SessionDep, meeting_id: UUID, current_user: CurrentUser):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check ownership
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    meeting.status = MeetingStatus.ENDED
    meeting.end_time = datetime.utcnow()
    
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting

@router.get("/", response_model=List[Meeting])
def list_meetings(db: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100):
    # If superuser, get all meetings, otherwise get only user's meetings
    if current_user.is_superuser:
        meetings = db.exec(select(Meeting).offset(skip).limit(limit)).all()
    else:
        meetings = db.exec(select(Meeting).where(Meeting.owner_id == current_user.id).offset(skip).limit(limit)).all()
    return meetings

@router.get("/{meeting_id}", response_model=Meeting)
def get_meeting(db: SessionDep, meeting_id: UUID, current_user: CurrentUser):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check ownership or superuser status
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return meeting

@router.delete("/{meeting_id}")
def delete_meeting(db: SessionDep, meeting_id: UUID, current_user: CurrentUser):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check ownership
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(meeting)
    db.commit()
    return {"message": "Meeting deleted successfully"} 