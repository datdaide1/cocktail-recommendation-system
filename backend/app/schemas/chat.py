from pydantic import BaseModel
<<<<<<< HEAD
from typing import List, Optional, Dict, Any

class MessageRequest(BaseModel):
    session_id: str
    content: str
    context: Optional[Dict[str, Any]] = None

class ActionBlock(BaseModel):
    type: str
    content: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None
    data: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[str]] = None

class MessageResponse(BaseModel):
    blocks: List[ActionBlock]
    quick_replies: Optional[List[str]] = None

class ToolCalculateCostRequest(BaseModel):
    recipe: List[Dict[str, Any]]

class SessionInitRequest(BaseModel):
    user_id: str
    mode: str
=======
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
>>>>>>> test
