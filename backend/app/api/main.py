from fastapi import APIRouter

from app.api.routes import (
    login, 
    users, 
    meetings, 
    transcriptions,
    ai_features
)

api_router = APIRouter()

# Authentication routes
api_router.include_router(login.router, prefix="/auth", tags=["auth"])
api_router.include_router(login.router, tags=["login"])  # Keep legacy login for compatibility

# User management routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Core meeting system routes
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])

# Real-time transcription routes (aligned with README API)
api_router.include_router(transcriptions.router, prefix="/meetings", tags=["transcriptions"])

# AI features routes (summarization, action items, search)
api_router.include_router(ai_features.router, prefix="/meetings", tags=["ai-features"])

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """
    Health check endpoint for the AI Meeting Assistant API
    """
    return {
        "status": "healthy",
        "service": "AI Meeting Assistant",
        "version": "1.0.0"
    }
