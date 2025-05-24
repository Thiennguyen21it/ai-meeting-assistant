"""
AI Meeting Assistant Services

This module contains all the AI and business logic services for the meeting assistant:
- Summarization: AI-powered meeting summary generation
- Action Items: AI extraction of tasks and action items from transcripts
- Transcription: Speech-to-text conversion services
- Search: Semantic search through meeting content
"""

from .summarization import generate_summary
from .action_items_service import extract_action_items, search_meeting_content
from .transcription import transcribe_audio

__all__ = [
    "generate_summary",
    "extract_action_items", 
    "search_meeting_content",
    "transcribe_audio"
] 