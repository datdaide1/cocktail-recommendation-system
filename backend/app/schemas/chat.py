from pydantic import BaseModel
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
