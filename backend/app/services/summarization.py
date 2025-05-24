import httpx
from app.core.config import settings
from app.models import SummaryLengthType
from typing import Optional

async def generate_summary(
    transcript_text: str, 
    length_type: SummaryLengthType,
    custom_prompt: Optional[str] = None
) -> str:
    """
    Generate a summary of the transcript using an AI service.
    
    Args:
        transcript_text: The text to summarize
        length_type: The desired length of the summary
        custom_prompt: Optional custom instructions for the AI
    """
    try:
        # Define prompts based on length type
        length_instructions = {
            SummaryLengthType.SHORT: "Create a very concise summary in 2-3 sentences.",
            SummaryLengthType.MEDIUM: "Create a summary in about 1-2 paragraphs.",
            SummaryLengthType.LONG: "Create a detailed summary covering all key points."
        }
        
        # Use custom prompt if provided, otherwise use length-based instruction
        instruction = custom_prompt if custom_prompt else length_instructions.get(
            length_type, 
            "Create a comprehensive summary of the following transcript."
        )
        
        # For OpenAI API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",  # Fixed typo in model name
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are a professional meeting summarizer. {instruction}"
                        },
                        {
                            "role": "user",
                            "content": f"Here is the meeting transcript to summarize:\n\n{transcript_text}"
                        }
                    ],
                    "temperature": 0.3,
                },
                timeout=60,
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                print(f"Summarization API error: {response.status_code} - {response.text}")
                return ""
                
    except Exception as e:
        print(f"Error in summarization service: {str(e)}")
        return "" 