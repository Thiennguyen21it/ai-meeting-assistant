from google import generativeai as genai
from typing import Optional
from app.core.config import settings
from app.models import SummaryLengthType

class SummaryService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
    async def generate_summary(self, transcript_content: str, length_type: SummaryLengthType) -> str:
        """
        Generate a summary of the transcript using Google Gemini.
        
        Args:
            transcript_content: The content of the transcript to summarize
            length_type: The desired length of the summary (SHORT, MEDIUM, DETAILED)
            
        Returns:
            The generated summary text
        """
        # Configure prompt based on length type
        if length_type == SummaryLengthType.SHORT:
            max_words = 100
            instruction = "Create a very concise summary highlighting only the key points."
        elif length_type == SummaryLengthType.MEDIUM:
            max_words = 250
            instruction = "Create a balanced summary covering the main topics discussed."
        else:  # DETAILED
            max_words = 500
            instruction = "Create a comprehensive summary that captures all significant details and nuances."
        
        # Create the prompt for Gemini
        prompt = f"""
        Please summarize the following transcript in approximately {max_words} words.
        {instruction}
        
        TRANSCRIPT:
        {transcript_content}
        """
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Gemini API không có phương thức generate_content_async
        # Sử dụng phương thức đồng bộ và bọc nó trong một hàm bất đồng bộ
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return f"Error generating summary: {str(e)}" 