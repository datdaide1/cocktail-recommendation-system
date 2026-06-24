from pydantic import BaseModel
from typing import List, Optional, Any

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    messages: List[Message]
    mode: str = "b2c"  # "b2c" or "b2b"

class ChatResponse(BaseModel):
    response: str
    rationale: Optional[str] = None
    data: Optional[Any] = None
