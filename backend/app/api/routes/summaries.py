from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Path
from sqlmodel import Session, select

from app.api.deps import CurrentUser,SessionDep
from app.models import (
    User, Meeting, Recording, Transcript, Summary, SummaryCreate, 
    SummaryPublic, SummariesPublic, SummaryLengthType
)
from app.services.summarization import generate_summary

router = APIRouter()


@router.post("/{transcript_id}", response_model=SummaryPublic)
async def create_summary(
    db: SessionDep,
    transcript_id: UUID,
    background_tasks: BackgroundTasks,
    summary_in: SummaryCreate,
    current_user: CurrentUser
) -> SummaryPublic:
    """
    Create a summary for a transcript.
    If content is provided, use that. Otherwise, generate a summary using AI.
    Custom prompt can be provided to guide the AI generation.
    """
    # Check if transcript exists
    transcript = db.get(Transcript, transcript_id)
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found",
        )
    
    # Check if user has access to the meeting
    recording = db.get(Recording, transcript.recording_id)
    meeting = db.get(Meeting, recording.meeting_id)
    if not meeting or meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Create summary with placeholder if content not provided
    content = summary_in.content
    is_generating = False
    
    if not content:
        is_generating = True
        content = "Generating summary..."
    
    # Create summary
    summary = Summary(
        transcript_id=transcript_id,
        content=content,
        length_type=summary_in.length_type,
    )
    
    db.add(summary)
    db.commit()
    db.refresh(summary)
    
    # If no content was provided, generate summary in the background
    if is_generating:
        background_tasks.add_task(
            generate_and_update_summary,
            db_session=db,
            summary_id=summary.id,
            transcript_text=transcript.content,
            length_type=summary_in.length_type,
            custom_prompt=summary_in.custom_prompt  # Pass custom prompt if provided
        )
    
    return SummaryPublic(
        id=summary.id,
        transcript_id=summary.transcript_id,
        content=summary.content,
        length_type=summary.length_type,
        created_at=summary.created_at,
    )


async def generate_and_update_summary(
    db_session: Session,
    summary_id: UUID,
    transcript_text: str,
    length_type: SummaryLengthType,
    custom_prompt: Optional[str] = None
):
    """
    Generate a summary using AI and update the database.
    A custom prompt can be provided to guide the generation.
    """
    try:
        # Generate summary
        summary_content = await generate_summary(transcript_text, length_type, custom_prompt)
        
        # Update summary in database
        summary = db_session.get(Summary, summary_id)
        if summary and summary_content:
            summary.content = summary_content
            db_session.add(summary)
            db_session.commit()
        else:
            print(f"Failed to generate or update summary {summary_id}")
    except Exception as e:
        print(f"Error generating summary: {str(e)}")


@router.get("/{transcript_id}", response_model=SummariesPublic)
def read_summaries(
    db: SessionDep,
    transcript_id: UUID,
    current_user: CurrentUser
) -> SummariesPublic:
    """
    Get all summaries for a transcript.
    """
    # Check if transcript exists
    transcript = db.get(Transcript, transcript_id)
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found",
        )
    
    # Check if user has access to the meeting
    recording = db.get(Recording, transcript.recording_id)
    meeting = db.get(Meeting, recording.meeting_id)
    if not meeting or meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get summaries
    summaries_query = select(Summary).where(Summary.transcript_id == transcript_id)
    summaries = db.exec(summaries_query).all()
    count = len(summaries)
    
    summaries_public = [
        SummaryPublic(
            id=summary.id,
            transcript_id=summary.transcript_id,
            content=summary.content,
            length_type=summary.length_type,
            created_at=summary.created_at,
        )
        for summary in summaries
    ]
    
    return SummariesPublic(data=summaries_public, count=count)

