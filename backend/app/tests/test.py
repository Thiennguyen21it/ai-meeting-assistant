import requests

response = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "Xin chào!",
    "chatbot_id": "test_bot",
    "session_id": None
})
print(response.json())