from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.orchestrator import run_orchestrator

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response = run_orchestrator(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
