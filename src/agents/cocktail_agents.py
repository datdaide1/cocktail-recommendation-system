import os
import json
import google.generativeai as genai
from src.utils.config import Config

# Define tool groups for dynamic routing
TOOL_GROUPS = {
    "discover": ["db_search_cocktails", "db_search_bars", "recommend_food_pairing"],
    "mixology": ["generate_custom_recipe", "substitute_ingredient", "calculate_abv", "calculate_cost_and_shopping_list"],
    "general": [] # No tools for general casual talk / chit-chat
}

# Define system instructions for both personas in structured XML format
GUEST_CONCIERGE_INSTRUCTION = """
<system_prompt>
  <agent>
    <name>Guest Concierge Agent</name>
    <organization>AI Lounge</organization>
    <persona>Warm, inviting, friendly, and sophisticated. Styled like a luxury hospitality host.</persona>
  </agent>
  
  <objective>
    Help customers find the perfect drink for their taste, mood, or occasion, and recommend real-world premium bars in Hanoi.
  </objective>
  
  <rules>
    <rule>Talk to the user naturally and understand their mood, taste preferences, or occasion.</rule>
    <rule>If they ask for cocktail suggestions or search for drinks (including abstract vibes/moods), use the tool `db_search_cocktails` by passing appropriate filters or passing their vibe query to the `query` argument.</rule>
    <rule>If they ask for places to go or bar suggestions in Hanoi, use the tool `db_search_bars` to find matching venues from our real-world local database.</rule>
    <rule>Always ground your drink and bar suggestions in the results returned by your tools. Do not invent non-existent bars or drinks.</rule>
    <rule>Do not copy-paste raw JSON data directly to the user. Always digest the database outputs and formulate a smooth, engaging, luxury response.</rule>
  </rules>
  
  <style_guidelines>
    <tone>Sophisticated, warm, polite, and elegant.</tone>
    <formatting>Use bullet points, bold drink names, and clean paragraphs. Avoid large blocks of text.</formatting>
  </style_guidelines>
</system_prompt>
"""

MASTER_BARTENDER_INSTRUCTION = """
<system_prompt>
  <agent>
    <name>Master Bartender Agent</name>
    <organization>AI Lounge</organization>
    <persona>Highly professional, technical, knowledgeable, and experienced in mixology.</persona>
  </agent>
  
  <objective>
    Help bartenders or home mixologists with precise recipes, mixing techniques, ingredient substitutions, custom signature drink creation, and ABV/cost calculations.
  </objective>
  
  <rules>
    <rule>Focus on the technical aspects of cocktails: exact measurements, proper glassware recommendations, garnishes, and methods (shaking, stirring, building, muddling).</rule>
    <rule>If the user wants to calculate the ABV of a customized drink, use the tool `calculate_abv`. Ask for volume and alcohol percentage of ingredients if missing.</rule>
    <rule>If the user is missing an ingredient, use the tool `substitute_ingredient` to suggest professional swaps and ratios.</rule>
    <rule>If they search for recipe details or ingredients, use `db_search_cocktails` to retrieve the database recipe.</rule>
    <rule>When asked to invent/sáng tạo a new custom recipe:
      1. First call `generate_custom_recipe` or `db_search_cocktails` using the requested ingredients/vibe to fetch reference baseline recipes from our database.
      2. Analyze the database reference ratios (alcohol vs acid vs sweetener) to ensure the new recipe is chemically balanced.
      3. Use your mixology expertise to name the new cocktail creatively, describe its garnish, and provide step-by-step instructions. Do not copy-paste existing drinks—sáng tạo a truly custom signature cocktail.
    </rule>
    <rule>Provide historical context or interesting stories about the cocktails to add depth and interest.</rule>
  </rules>
  
  <style_guidelines>
    <tone>Professional, precise, clear, and informative.</tone>
    <formatting>Use bold headers, numbered lists for steps, and clean tables or markdown lists for recipes.</formatting>
  </style_guidelines>
</system_prompt>
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
            if Config.CUSTOM_API_KEY:
                provider = "custom"
            elif Config.OPENROUTER_API_KEY:
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
            
        # Import and hold references to all available tools
        from src.tools import (
            db_search_cocktails,
            db_search_bars,
            calculate_abv,
            substitute_ingredient,
            calculate_cost_and_shopping_list,
            generate_custom_recipe,
            recommend_food_pairing
        )
        self.tools = [
            db_search_cocktails,
            db_search_bars,
            calculate_abv,
            substitute_ingredient,
            calculate_cost_and_shopping_list,
            generate_custom_recipe,
            recommend_food_pairing
        ]
        
    def get_agent_model(self, role: str, active_tools: list):
        """
        Creates a GenerativeModel configured for a specific role and active tools.
        """
        if role == "bartender":
            instruction = MASTER_BARTENDER_INSTRUCTION
        else:
            instruction = GUEST_CONCIERGE_INSTRUCTION
            
        return genai.GenerativeModel(
            model_name=Config.GEMINI_MODEL,
            tools=active_tools if active_tools else None,
            system_instruction=instruction
        )

    def classify_query(self, user_message: str) -> str:
        """
        Uses a quick zero-shot classification to route the query to 'discover', 'mixology', or 'general'.
        """
        prompt = f"""You are the Tool Router for AI Lounge.
Classify the user's request into one of these categories:
- 'discover': if they are searching for existing cocktails, recipes, bars, venues, locations, or food pairings.
- 'mixology': if they want to calculate ABV, substitute ingredients, create new custom recipes, calculate shopping cost, or need mixing advice.
- 'general': if it is just greeting, casual chat, or general question.

Output ONLY the category name: 'discover', 'mixology', or 'general'. Do not write anything else.

User Request: {user_message}
Category:"""
        
        try:
            if self.provider == "gemini":
                # Quick call to Gemini without tool definitions
                model = genai.GenerativeModel("gemini-3.1-flash-lite")
                response = model.generate_content(prompt)
                category = response.text.strip().lower()
            else:
                # OpenAI/OpenRouter quick call
                import requests
                if self.provider == "openrouter":
                    url = "https://openrouter.ai/api/v1/chat/completions"
                    api_key = Config.OPENROUTER_API_KEY
                    model_name = Config.OPENROUTER_MODEL or "google/gemini-2.5-flash"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                elif self.provider == "custom":
                    url = Config.CUSTOM_API_BASE or "http://127.0.0.1:20128/v1"
                    if not url.endswith("/chat/completions"):
                        url = url.rstrip("/") + "/chat/completions"
                    api_key = Config.CUSTOM_API_KEY
                    model_name = Config.CUSTOM_MODEL or "beeknoee/gemini-3.5-flash"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                else:
                    url = "https://api.openai.com/v1/chat/completions"
                    api_key = Config.OPENAI_API_KEY
                    model_name = Config.OPENAI_MODEL or "gpt-4o-mini"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}]
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=10)
                if resp.status_code == 200:
                    res_data = resp.json()
                    category = res_data["choices"][0]["message"]["content"].strip().lower()
                else:
                    category = "general"
        except Exception as e:
            print(f"Routing failed: {e}. Defaulting to 'general'.")
            category = "general"
            
        # Standardize return
        if "discover" in category:
            return "discover"
        elif "mixology" in category:
            return "mixology"
        else:
            return "general"

    def run_chat(self, user_message: str, chat_history: list, role: str) -> dict:
        """
        Routes the chat turn to the active LLM provider.
        """
        if self.provider == "gemini":
            return self.run_chat_gemini(user_message, chat_history, role)
        else:
            # OpenAI, OpenRouter, or Custom
            return self.run_chat_openai_compatible(user_message, chat_history, role)

    def run_chat_gemini(self, user_message: str, chat_history: list, role: str) -> dict:
        """
        Executes a turn using Gemini native SDK with dynamic tool subsets.
        """
        try:
            category = self.classify_query(user_message)
            print(f"[Tool Router] Classified query as: {category}")
            active_tool_names = TOOL_GROUPS.get(category, [])
            active_tools = [t for t in self.tools if t.__name__ in active_tool_names]
            
            model = self.get_agent_model(role, active_tools)
            
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
            
            # Import execute_tool dispatcher
            from src.tools import execute_tool
            
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

    def run_chat_openai_compatible(self, user_message: str, chat_history: list, role: str) -> dict:
        """
        Executes a turn using OpenAI-compatible HTTP requests (OpenAI/OpenRouter/Custom) with dynamic tool subsets.
        """
        import requests
        
        try:
            category = self.classify_query(user_message)
            print(f"[Tool Router] Classified query as: {category}")
            active_tool_names = TOOL_GROUPS.get(category, [])
            
            if self.provider == "openrouter":
                url = "https://openrouter.ai/api/v1/chat/completions"
                api_key = Config.OPENROUTER_API_KEY
                model_name = Config.OPENROUTER_MODEL or "google/gemini-2.5-flash"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/datdaide1/cocktail-recommendation-system",
                    "X-Title": "AI Cocktail Lounge"
                }
            elif self.provider == "custom":
                url = Config.CUSTOM_API_BASE or "http://127.0.0.1:20128/v1"
                if not url.endswith("/chat/completions"):
                    url = url.rstrip("/") + "/chat/completions"
                api_key = Config.CUSTOM_API_KEY
                model_name = Config.CUSTOM_MODEL or "beeknoee/gemini-3.5-flash"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
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
            from src.tools import TOOL_DECLARATIONS, execute_tool
            openai_tools = []
            for tool in TOOL_DECLARATIONS:
                if tool["name"] not in active_tool_names:
                    continue
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
                    "messages": messages
                }
                if openai_tools:
                    payload["tools"] = openai_tools
                    payload["tool_choice"] = "auto"
                
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
