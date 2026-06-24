from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage

# Placeholder for LangGraph Workflow
async def run_agent_workflow(session_id: str, content: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    # In a real implementation, this would use LangGraph to route
    # between b2c_mixologist and b2b_bartender based on the session history/mode.
    # For now, we return a mock Server-Driven UI response.
    
    return [
        {
            "type": "text",
            "content": "Tôi đã tìm thấy thông tin bạn cần. Vui lòng xem các gợi ý dưới đây:"
        },
        {
            "type": "carousel_venues",
            "items": [
                {
                    "name": "Mock Bar",
                    "rationale": "✨ Lý do: Đây là kết quả mock từ kiến trúc mới."
                }
            ]
        }
    ]
