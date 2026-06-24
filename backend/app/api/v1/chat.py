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
