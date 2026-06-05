import os
import json
import google.generativeai as genai
from src.utils.config import Config
from src.tools.cocktail_tools import (
    db_search_cocktails,
    db_search_bars,
    calculate_abv,
    substitute_ingredient,
    execute_tool
)

# Define system instructions for both personas
GUEST_CONCIERGE_INSTRUCTION = """
You are the Guest Concierge Agent for "AI Lounge". 
Your persona is warm, inviting, friendly, and sophisticated.
You help customers find the perfect drink for their taste/mood and recommend real-world premium bars in Vietnam (Hanoi/HCMC).

Rules:
1. Talk to the user naturally and understand their mood, taste preferences, or occasion.
2. If they ask for cocktail recommendations, use the tool `db_search_cocktails` to retrieve matching drinks from our database.
3. If they ask for places to go or bar suggestions in Vietnam, use the tool `db_search_bars` to find matching venues from our real-world local database.
4. Always ground your drink and bar suggestions in the results returned by your tools. Do not invent non-existent bars or drinks.
5. Keep your responses concise, elegant, and styled like a luxury hospitality host.
"""

MASTER_BARTENDER_INSTRUCTION = """
You are the Master Bartender Agent for "AI Lounge".
Your persona is highly professional, technical, knowledgeable, and experienced in mixology.
You help bartenders (or home mixologists) with precise recipes, mixing techniques, ingredient substitutions, and ABV calculations.

Rules:
1. Focus on the technical aspect of cocktails: exact measurements, glassware, garnish, and methods (shaking, stirring, building, muddling).
2. If the user wants to calculate the ABV of a customized drink, use the tool `calculate_abv`. Make sure to ask for the ml volume and alcohol percentage of the ingredients if not provided.
3. If the user is missing an ingredient, use the tool `substitute_ingredient` to suggest professional swaps and ratios.
4. If they search for recipe details, use `db_search_cocktails` to get the database recipe.
5. Provide historical context or interesting stories about the cocktails to add depth to your response.
6. Keep your responses structured, clear, and professional.
"""

class CocktailAgentSystem:
    """
    Main controller for the Multi-Agent System using Gemini API.
    Dynamically routes queries and runs a robust manual function calling loop.
    """
    def __init__(self):
        # Configure Gemini API
        api_key = Config.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment configurations.")
        genai.configure(api_key=api_key)
        
        # Define tools for model declaration
        self.tools = [
            db_search_cocktails,
            db_search_bars,
            calculate_abv,
            substitute_ingredient
        ]
        
    def get_agent_model(self, role: str):
        """
        Creates a GenerativeModel configured for a specific role and its tools.
        """
        if role == "bartender":
            instruction = MASTER_BARTENDER_INSTRUCTION
        else:
            instruction = GUEST_CONCIERGE_INSTRUCTION
            
        return genai.GenerativeModel(
            model_name=Config.GEMINI_MODEL,
            tools=self.tools,
            system_instruction=instruction
        )

    def run_chat(self, user_message: str, chat_history: list, role: str) -> dict:
        """
        Executes a turn in the chat session, manually executing tool calls in a loop.
        
        Args:
            user_message: The message sent by the user.
            chat_history: History format of list of {"role": "user"|"model", "parts": [str]}
            role: The selected role ('guest' or 'bartender')
            
        Returns:
            dict containing response text and the updated chat history.
        """
        try:
            model = self.get_agent_model(role)
            
            # Format chat history for Gemini SDK
            gemini_history = []
            for msg in chat_history:
                gemini_history.append(
                    genai.protos.Content(
                        role=msg["role"],
                        parts=[genai.protos.Part(text=msg["parts"][0])]
                    )
                )
                
            # Start chat session
            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(user_message)
            
            # Manual function calling loop (supporting up to 5 rounds of tool execution)
            for round_idx in range(5):
                function_calls = []
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.function_call and part.function_call.name:
                            function_calls.append(part.function_call)
                            
                if not function_calls:
                    break  # No tool calls needed, we have the final text response
                    
                # Execute all requested functions in parallel/sequence
                function_responses = []
                for fc in function_calls:
                    func_name = fc.name
                    func_args = dict(fc.args) if fc.args else {}
                    
                    try:
                        result_str = execute_tool(func_name, func_args)
                        result_json = json.loads(result_str)
                    except Exception as e:
                        result_json = {"error": f"Tool execution failed: {str(e)}"}
                        
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=func_name,
                                response=result_json
                            )
                        )
                    )
                
                # Append the function execution results to chat history
                chat.history.append(
                    genai.protos.Content(
                        role="function",
                        parts=function_responses
                    )
                )
                
                # Generate new content based on updated history with tools
                response = model.generate_content(chat.history)
                
            # Append final text response to chat history
            if response.candidates and response.candidates[0].content:
                chat.history.append(response.candidates[0].content)
                
            # Filter and construct clean chat history for UI (ignoring raw tool call blocks)
            updated_history = []
            for content in chat.history:
                text_parts = [part.text for part in content.parts if part.text]
                if text_parts:
                    updated_history.append({
                        "role": content.role,
                        "parts": [text_parts[0]]
                    })
                    
            # Extract final text message
            final_text = ""
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        final_text += part.text
                        
            return {
                "message": final_text,
                "chat_history": updated_history
            }
            
        except Exception as e:
            print(f"Error in CocktailAgentSystem.run_chat: {e}")
            return {
                "message": f"Sorry, I encountered an issue: {str(e)}. Please try again.",
                "chat_history": chat_history + [
                    {"role": "user", "parts": [user_message]},
                    {"role": "model", "parts": [f"Error occurred: {str(e)}"]}
                ]
            }
