from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from app.api.deps import SessionDep, CurrentUser
from app.models import (
    Meeting, Recording, Transcript, Summary, SummaryCreate, SummaryPublic,
    ActionItem, ActionItemCreate, ActionItemPublic, ActionItemsPublic,
    SummaryLengthType, Message
)
from app.services.summarization import generate_summary
from app.services.action_items_service import extract_action_items

router = APIRouter()


@router.post("/{meeting_id}/summarize", response_model=SummaryPublic)
async def generate_meeting_summary(
    meeting_id: UUID,
    summary_request: SummaryCreate,
    session: SessionDep,
    current_user: CurrentUser
) -> SummaryPublic:
    """
    Generate an AI-powered summary of a meeting
    """
    # Verify meeting exists and user has access
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get all transcripts for this meeting
    recordings = session.exec(
        select(Recording).where(Recording.meeting_id == meeting_id)
    ).all()
    
    # Combine all transcript content
    all_transcript_text = ""
    transcript_ids = []
    
    for recording in recordings:
        transcripts = session.exec(
            select(Transcript).where(Transcript.recording_id == recording.id)
        ).all()
        for transcript in transcripts:
            all_transcript_text += transcript.content + "\n"
            transcript_ids.append(transcript.id)
    
    if not all_transcript_text.strip():
        raise HTTPException(
            status_code=400, 
            detail="No transcriptions available for this meeting"
        )
    
    # Generate summary using AI service
    if summary_request.content:
        # Use provided content
        summary_content = summary_request.content
    else:
        # Generate using AI
        summary_content = await generate_summary(
            all_transcript_text, 
            summary_request.length_type
        )
        
        if not summary_content:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate summary"
            )
    
    # Use the last transcript ID for the relationship
    # In a more sophisticated implementation, you might create a meeting-level summary
    if not transcript_ids:
        raise HTTPException(
            status_code=400,
            detail="No transcripts found to link summary to"
        )
    
    # Create summary record
    summary = Summary(
        content=summary_content,
        length_type=summary_request.length_type,
        transcript_id=transcript_ids[-1],  # Link to the last transcript
        created_at=datetime.now()
    )
    
    session.add(summary)
    session.commit()
    session.refresh(summary)
    
    return SummaryPublic(
        id=summary.id,
        transcript_id=summary.transcript_id,
        content=summary.content,
        length_type=summary.length_type,
        created_at=summary.created_at
    )


@router.post("/{meeting_id}/action-items", response_model=ActionItemsPublic)
async def extract_meeting_action_items(
    meeting_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> ActionItemsPublic:
    """
    Extract action items from meeting transcriptions using AI
    """
    # Verify meeting exists and user has access
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get all transcripts for this meeting
    recordings = session.exec(
        select(Recording).where(Recording.meeting_id == meeting_id)
    ).all()
    
    # Combine all transcript content
    all_transcript_text = ""
    for recording in recordings:
        transcripts = session.exec(
            select(Transcript).where(Transcript.recording_id == recording.id)
        ).all()
        for transcript in transcripts:
            all_transcript_text += transcript.content + "\n"
    
    if not all_transcript_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No transcriptions available for this meeting"
        )
    
    # Extract action items using AI service
    action_items_data = await extract_action_items(all_transcript_text, str(meeting_id))
    
    if not action_items_data:
        return ActionItemsPublic(data=[], count=0)
    
    # Save action items to database
    created_items = []
    for item_data in action_items_data:
        action_item = ActionItem(
            title=item_data["title"],
            description=item_data.get("description"),
            assignee=item_data.get("assignee"),
            due_date=item_data.get("due_date"),
            status=item_data["status"],
            meeting_id=meeting_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        session.add(action_item)
        created_items.append(action_item)
    
    session.commit()
    
    # Refresh all items to get their IDs
    for item in created_items:
        session.refresh(item)
    
    # Convert to public format
    action_items_public = [
        ActionItemPublic(
            id=item.id,
            title=item.title,
            description=item.description,
            assignee=item.assignee,
            due_date=item.due_date,
            status=item.status,
            meeting_id=item.meeting_id,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        for item in created_items
    ]
    
    return ActionItemsPublic(data=action_items_public, count=len(action_items_public))


@router.get("/{meeting_id}/action-items", response_model=ActionItemsPublic)
async def get_meeting_action_items(
    meeting_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
) -> ActionItemsPublic:
    """
    Get existing action items for a meeting
    """
    # Verify meeting exists and user has access
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get action items for this meeting
    action_items = session.exec(
        select(ActionItem)
        .where(ActionItem.meeting_id == meeting_id)
        .offset(skip)
        .limit(limit)
    ).all()
    
    # Convert to public format
    action_items_public = [
        ActionItemPublic(
            id=item.id,
            title=item.title,
            description=item.description,
            assignee=item.assignee,
            due_date=item.due_date,
            status=item.status,
            meeting_id=item.meeting_id,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        for item in action_items
    ]
    
    return ActionItemsPublic(data=action_items_public, count=len(action_items_public))


@router.get("/{meeting_id}/summaries", response_model=List[SummaryPublic])
async def get_meeting_summaries(
    meeting_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> List[SummaryPublic]:
    """
    Get existing summaries for a meeting
    """
    # Verify meeting exists and user has access
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get all recordings and their transcripts for this meeting
    recordings = session.exec(
        select(Recording).where(Recording.meeting_id == meeting_id)
    ).all()
    
    summaries = []
    for recording in recordings:
        transcripts = session.exec(
            select(Transcript).where(Transcript.recording_id == recording.id)
        ).all()
        
        for transcript in transcripts:
            transcript_summaries = session.exec(
                select(Summary).where(Summary.transcript_id == transcript.id)
            ).all()
            summaries.extend(transcript_summaries)
    
    # Convert to public format
    summaries_public = [
        SummaryPublic(
            id=summary.id,
            transcript_id=summary.transcript_id,
            content=summary.content,
            length_type=summary.length_type,
            created_at=summary.created_at
        )
        for summary in summaries
    ]
    
    return summaries_public 