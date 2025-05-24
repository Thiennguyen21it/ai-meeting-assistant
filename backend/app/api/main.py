from fastapi import APIRouter

from app.api.routes import (
    items, 
    login, 
    users, 
    utils, 
    meetings, 
    recordings, 
    transcripts,
    summaries
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
# api_router.include_router(items.router, prefix="/items", tags=["items"])
# api_router.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# Add new meeting recording system routes
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(recordings.router, prefix="/recordings", tags=["recordings"])
api_router.include_router(transcripts.router, prefix="/transcripts", tags=["transcripts"])
api_router.include_router(summaries.router, prefix="/summaries", tags=["summaries"])
