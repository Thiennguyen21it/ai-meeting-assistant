import os
import httpx
from pathlib import Path
from app.core.config import settings

async def transcribe_audio(file_path: str) -> str:
    """
    Transcribe an audio file to text using an external service.
    
    This function can be implemented with various speech-to-text services:
    - OpenAI Whisper API
    - Google Cloud Speech-to-Text
    - Azure Speech Services
    - Local Whisper model
    
    For this implementation, we'll use OpenAI's Whisper API as an example.
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""
        
        # For OpenAI Whisper API
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                # You can adjust the model based on your needs
                # Available models: whisper-1
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
                    },
                    files={
                        "file": f,
                    },
                    data={
                        "model": "whisper-1",
                        "language": "en",  # You can make this configurable
                    },
                    timeout=300,  # Longer timeout for large files
                )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "")
            else:
                print(f"Transcription API error: {response.status_code} - {response.text}")
                return ""
                
    except Exception as e:
        print(f"Error in transcription service: {str(e)}")
        return "" 