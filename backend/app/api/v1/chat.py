<<<<<<< HEAD
from fastapi import APIRouter
from app.schemas.chat import MessageRequest, MessageResponse, SessionInitRequest
from app.agents.orchestrator import run_agent_workflow

router = APIRouter()

@router.post("/session/init")
async def init_session(req: SessionInitRequest):
    return {
        "session_id": f"sess_{req.user_id}",
        "welcome_message": "Chào buổi tối, The Mixologist đã sẵn sàng phục vụ bạn...",
        "suggested_prompts": ["Gợi ý quán đi Date", "Tôi muốn uống vị chua"]
    }

@router.post("/message", response_model=MessageResponse)
async def chat_message(req: MessageRequest):
    # Route through LangGraph orchestrator
    response_blocks = await run_agent_workflow(req.session_id, req.content, req.context)
    return MessageResponse(blocks=response_blocks)
=======
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
>>>>>>> test
