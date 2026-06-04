import os
from src.utils.config import Config
from src.tools.cocktail_tools import TOOL_DECLARATIONS, execute_tool

class CocktailAgentSystem:
    """
    Skeleton class for the Cocktail Multi-Agent System.
    This manages the Orchestrator, Guest Concierge Agent, and Master Bartender Agent.
    """
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = Config.GEMINI_MODEL
        # SKELETON: To be implemented in the next phase.
        pass

    def run_chat(self, user_message: str, chat_history: list, role: str) -> dict:
        """
        Runs the chat session and decides whether to route and invoke tools.
        
        Args:
            user_message: The message from the user
            chat_history: Past conversation messages
            role: Current selected role ('guest' or 'bartender')
            
        Returns:
            dict containing response message and updated chat history
        """
        # SKELETON: To be filled during implementation phase.
        # This will use Gemini API with function calling to execute tools from cocktail_tools.py.
        return {
            "message": f"[Skeleton Response] Bạn đang ở vai trò {role.upper()}. Lõi xử lý Agents sẽ được viết ở đây trong bước tiếp theo.",
            "chat_history": chat_history + [
                {"role": "user", "parts": [user_message]},
                {"role": "model", "parts": [f"Phản hồi mẫu từ Agent ở chế độ {role}"]}
            ]
        }
