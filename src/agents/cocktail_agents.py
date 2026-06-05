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
    Main controller for the Multi-Agent System.
    Supports Google Gemini, OpenAI, and OpenRouter with automatic tool execution.
    """
    def __init__(self):
        # Determine active provider
        provider = Config.LLM_PROVIDER
        if not provider:
            # Auto-detect by checking configured keys
            if Config.OPENROUTER_API_KEY:
                provider = "openrouter"
            elif Config.OPENAI_API_KEY:
                provider = "openai"
            elif Config.GEMINI_API_KEY:
                provider = "gemini"
            else:
                provider = "gemini"
                
        self.provider = provider
        print(f"Initializing CocktailAgentSystem with provider: {self.provider}")
        
        # Configure Gemini SDK if active
        if self.provider == "gemini":
            api_key = Config.GEMINI_API_KEY
            if not api_key:
                raise ValueError("Active provider is Gemini but GEMINI_API_KEY is not configured in .env.")
            genai.configure(api_key=api_key)
            
        # Define tools for native model configuration
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
        Routes the chat turn to the active LLM provider.
        """
        if self.provider == "gemini":
            return self.run_chat_gemini(user_message, chat_history, role)
        else:
            # OpenAI or OpenRouter
            is_openrouter = (self.provider == "openrouter")
            return self.run_chat_openai_compatible(user_message, chat_history, role, is_openrouter)

    def run_chat_gemini(self, user_message: str, chat_history: list, role: str) -> dict:
        """
        Executes a turn using Gemini native SDK.
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
                    break
                    
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
                
                chat.history.append(
                    genai.protos.Content(
                        role="function",
                        parts=function_responses
                    )
                )
                
                response = model.generate_content(chat.history)
                
            if response.candidates and response.candidates[0].content:
                chat.history.append(response.candidates[0].content)
                
            updated_history = []
            for content in chat.history:
                text_parts = [part.text for part in content.parts if part.text]
                if text_parts:
                    updated_history.append({
                        "role": content.role,
                        "parts": [text_parts[0]]
                    })
                    
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
            print(f"Error in CocktailAgentSystem.run_chat_gemini: {e}")
            return {
                "message": f"Sorry, I encountered an issue: {str(e)}. Please try again.",
                "chat_history": chat_history + [
                    {"role": "user", "parts": [user_message]},
                    {"role": "model", "parts": [f"Error occurred: {str(e)}"]}
                ]
            }

    def run_chat_openai_compatible(self, user_message: str, chat_history: list, role: str, is_openrouter: bool = False) -> dict:
        """
        Executes a turn using OpenAI-compatible HTTP requests (OpenAI/OpenRouter).
        """
        import requests
        
        try:
            if is_openrouter:
                url = "https://openrouter.ai/api/v1/chat/completions"
                api_key = Config.OPENROUTER_API_KEY
                model_name = Config.OPENROUTER_MODEL or "google/gemini-2.5-flash"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/datdaide1/cocktail-recommendation-system",
                    "X-Title": "AI Cocktail Lounge"
                }
            else:
                url = "https://api.openai.com/v1/chat/completions"
                api_key = Config.OPENAI_API_KEY
                model_name = Config.OPENAI_MODEL or "gpt-4o-mini"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
            if not api_key:
                raise ValueError(f"API key not found for provider '{self.provider}'. Check your .env configuration.")
                
            system_instruction = MASTER_BARTENDER_INSTRUCTION if role == "bartender" else GUEST_CONCIERGE_INSTRUCTION
            
            # Construct standard chat completions message list
            messages = [{"role": "system", "content": system_instruction.strip()}]
            
            for msg in chat_history:
                role_map = {"user": "user", "model": "assistant"}
                messages.append({
                    "role": role_map.get(msg["role"], "user"),
                    "content": msg["parts"][0]
                })
                
            messages.append({"role": "user", "content": user_message})
            
            # Build tool definitions compliant with OpenAI / OpenRouter schemas
            from src.tools.cocktail_tools import TOOL_DECLARATIONS
            openai_tools = []
            for tool in TOOL_DECLARATIONS:
                properties = {}
                for prop, val in tool["parameters"].get("properties", {}).items():
                    properties[prop] = {
                        "type": val.get("type", "STRING").lower(),
                        "description": val.get("description", "")
                    }
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": tool["parameters"].get("required", [])
                        }
                    }
                })
                
            # Manual function calling loop
            for round_idx in range(5):
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "tools": openai_tools,
                    "tool_choice": "auto"
                }
                
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
                if resp.status_code != 200:
                    raise Exception(f"API error from '{self.provider}' ({resp.status_code}): {resp.text}")
                    
                res_data = resp.json()
                choice = res_data["choices"][0]
                assistant_msg = choice["message"]
                
                # Append assistant response to messages for history tracking
                messages.append(assistant_msg)
                
                tool_calls = assistant_msg.get("tool_calls")
                if not tool_calls:
                    break  # Final text response returned
                    
                # Execute tool responses
                for tc in tool_calls:
                    tc_id = tc["id"]
                    func_name = tc["function"]["name"]
                    func_args_str = tc["function"]["arguments"]
                    
                    try:
                        func_args = json.loads(func_args_str) if func_args_str else {}
                    except Exception as e:
                        func_args = {}
                        
                    try:
                        result_str = execute_tool(func_name, func_args)
                    except Exception as e:
                        result_str = json.dumps({"error": f"Tool execution failed: {str(e)}"})
                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "name": func_name,
                        "content": result_str
                    })
                    
            # Retrieve final message content
            final_text = messages[-1].get("content") or ""
            if not final_text:
                # Traverse backward if the last turn was a tool call response
                for msg in reversed(messages):
                    if msg.get("role") == "assistant" and msg.get("content"):
                        final_text = msg["content"]
                        break
                        
            # Format history for UI
            new_history = list(chat_history)
            new_history.append({"role": "user", "parts": [user_message]})
            new_history.append({"role": "model", "parts": [final_text]})
            
            return {
                "message": final_text,
                "chat_history": new_history
            }
            
        except Exception as e:
            print(f"Error in CocktailAgentSystem.run_chat_openai_compatible: {e}")
            return {
                "message": f"Sorry, I encountered an issue: {str(e)}. Please check your provider configuration.",
                "chat_history": chat_history + [
                    {"role": "user", "parts": [user_message]},
                    {"role": "model", "parts": [f"Error occurred: {str(e)}"]}
                ]
            }
