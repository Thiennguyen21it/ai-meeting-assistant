import httpx
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings
from app.models import ActionItemCreate, ActionItemStatus


async def extract_action_items(transcript_text: str, meeting_id: str) -> List[Dict[str, Any]]:
    """
    Extract action items from meeting transcript using AI.
    
    Args:
        transcript_text: The meeting transcript text
        meeting_id: The meeting ID these action items belong to
        
    Returns:
        List of action item dictionaries
    """
    try:
        system_prompt = """
        You are an expert at analyzing meeting transcripts and extracting actionable items.
        
        Please analyze the following meeting transcript and extract all action items, tasks, and follow-ups.
        For each action item, provide:
        - title: A clear, concise title (max 100 characters)
        - description: Detailed description of what needs to be done
        - assignee: The person responsible (if mentioned, otherwise null)
        - due_date: Estimated due date if mentioned or implied (ISO format)
        - status: Always set to "PENDING" for new items
        
        Return the results as a JSON array. If no action items are found, return an empty array.
        
        Example format:
        [
            {
                "title": "Prepare Q4 budget report",
                "description": "Create comprehensive budget analysis for Q4 including projections and variance analysis",
                "assignee": "John Smith",
                "due_date": "2024-01-15T00:00:00",
                "status": "PENDING"
            }
        ]
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": f"Meeting transcript to analyze:\n\n{transcript_text}"
                        }
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                },
                timeout=60,
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                try:
                    # Parse the JSON response
                    action_items_data = json.loads(content)
                    
                    # Handle both array and object responses
                    if isinstance(action_items_data, dict) and "action_items" in action_items_data:
                        action_items_data = action_items_data["action_items"]
                    elif not isinstance(action_items_data, list):
                        action_items_data = []
                    
                    # Process and validate each action item
                    processed_items = []
                    for item in action_items_data:
                        # Parse due_date if provided
                        due_date = None
                        if item.get("due_date"):
                            try:
                                due_date = datetime.fromisoformat(item["due_date"].replace("Z", "+00:00"))
                            except:
                                # If parsing fails, set a default due date (1 week from now)
                                due_date = datetime.now() + timedelta(weeks=1)
                        
                        processed_item = {
                            "title": item.get("title", "Untitled Action Item")[:255],
                            "description": item.get("description"),
                            "assignee": item.get("assignee"),
                            "due_date": due_date,
                            "status": ActionItemStatus.PENDING,
                            "meeting_id": meeting_id
                        }
                        processed_items.append(processed_item)
                    
                    return processed_items
                    
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON response: {content}")
                    return []
            else:
                print(f"Action items extraction API error: {response.status_code} - {response.text}")
                return []
                
    except Exception as e:
        print(f"Error in action items extraction service: {str(e)}")
        return []


async def search_meeting_content(query: str, transcript_text: str) -> Dict[str, Any]:
    """
    Search through meeting content using AI-powered semantic search.
    
    Args:
        query: The search query
        transcript_text: The meeting transcript to search through
        
    Returns:
        Dictionary with search results and relevant excerpts
    """
    try:
        system_prompt = f"""
        You are a meeting content search assistant. The user will provide a search query and you need to find relevant information from the meeting transcript.
        
        Search query: "{query}"
        
        Please analyze the transcript and return:
        1. A relevance score (0-10) indicating how well the transcript matches the query
        2. Key excerpts (max 3) that are most relevant to the query
        3. A summary of findings related to the query
        4. Timestamps if available (look for time indicators in the text)
        
        Return as JSON in this format:
        {{
            "relevance_score": 8,
            "excerpts": [
                {{"text": "relevant excerpt 1", "timestamp": "10:30"}},
                {{"text": "relevant excerpt 2", "timestamp": "15:45"}}
            ],
            "summary": "Brief summary of what was found related to the query",
            "total_matches": 2
        }}
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": f"Meeting transcript to search:\n\n{transcript_text}"
                        }
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                },
                timeout=60,
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                try:
                    search_results = json.loads(content)
                    return search_results
                except json.JSONDecodeError:
                    print(f"Failed to parse search results JSON: {content}")
                    return {
                        "relevance_score": 0,
                        "excerpts": [],
                        "summary": "Failed to process search results",
                        "total_matches": 0
                    }
            else:
                print(f"Search API error: {response.status_code} - {response.text}")
                return {
                    "relevance_score": 0,
                    "excerpts": [],
                    "summary": "Search service temporarily unavailable",
                    "total_matches": 0
                }
                
    except Exception as e:
        print(f"Error in search service: {str(e)}")
        return {
            "relevance_score": 0,
            "excerpts": [],
            "summary": f"Search error: {str(e)}",
            "total_matches": 0
        } 