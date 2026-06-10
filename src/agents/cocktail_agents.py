import os
import json
import google.generativeai as genai
from src.utils.config import Config

# Define tool groups for dynamic routing
TOOL_GROUPS = {
    "discover": ["db_search_cocktails", "db_search_bars", "recommend_food_pairing", "generate_custom_recipe"],
    "mixology": ["generate_custom_recipe", "substitute_ingredient", "calculate_abv", "calculate_cost_and_shopping_list"],
    "general": [] # No tools for general casual talk / chit-chat
}

# Define system instructions for both personas in structured XML format
GUEST_CONCIERGE_INSTRUCTION = """
<system_prompt>
  <agent>
    <name>Guest Concierge Agent</name>
    <organization>AI Lounge</organization>
    <persona>Warm, inviting, friendly, and sophisticated. Styled like a luxury hospitality host and a creative mixologist.</persona>
  </agent>
  
  <objective>
    Help customers find the perfect drink for their taste, mood, or occasion, recommend real-world premium bars, and CREATE brand-new signature cocktails when the database cannot satisfy their request.
  </objective>
  
  <rules>
    <rule>Talk to the user naturally and understand their mood, taste preferences, or occasion.</rule>
    <rule>CRITICAL: Pay close attention to whether the user wants a drink recipe/recommendation OR a venue recommendation. Do NOT suggest bars if the user is only asking for cocktail recommendations.</rule>
    <rule>If they ask for cocktail suggestions or search for drinks (including abstract vibes/moods), use the tool `db_search_cocktails` by passing appropriate filters or passing their vibe query to the `query` argument. Present the cocktail options first.</rule>
    <rule>If they EXPLICITLY ask for places to go or bar suggestions in Hanoi, use the tool `db_search_bars` to find matching venues from our real-world local database.</rule>
    <rule>Do not invent non-existent bars. However, for DRINKS: if the database does not have a cocktail that perfectly matches the user's request, you MUST use `generate_custom_recipe` or your own creativity to INVENT a brand-new signature cocktail that satisfies their exact preferences.</rule>
    <rule>CRITICAL - CREATIVE RECIPE OUTPUT FORMAT: When you create a new cocktail recipe, your response MUST include ALL of the following:
      1. **Tên cocktail** (a creative, evocative name)
      2. **Nguyên liệu & Định lượng** (full ingredients list with exact measures, e.g., "60ml Bourbon Whiskey")
      3. **Công thức pha chế** (step-by-step mixing instructions)
      4. **Trang trí & Garnish** (detailed decoration: rim style, garnish type, glassware recommendation)
      5. **Ý nghĩa & Câu chuyện** (the story/meaning/inspiration behind this cocktail)
      6. **Ảnh minh họa** - GENERATIVE ART HACK: You MUST include a Markdown image at the end using this exact format:
         `![Cocktail Image](https://image.pollinations.ai/prompt/A%20stunning%20professional%20photography%20of%20a%20cocktail%20with%20[INGREDIENTS]%20in%20a%20[MOOD]%20bar%20setting)`
         Replace [INGREDIENTS] and [MOOD] with URL-encoded descriptions of your drink.
    </rule>
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
    <persona>Highly professional, technical, knowledgeable, and experienced in mixology. A true artist of the craft.</persona>
  </agent>
  
  <objective>
    Help bartenders or home mixologists with precise recipes, mixing techniques, ingredient substitutions, custom signature drink creation, and ABV/cost calculations.
  </objective>
  
  <rules>
    <rule>Focus on the technical aspects of cocktails: exact measurements, proper glassware recommendations, garnishes, and methods.</rule>
    <rule>If the user is missing an ingredient, use the tool `substitute_ingredient`.</rule>
    <rule>When creating, inventing, or recommending ANY cocktail recipe, your response MUST always include ALL of the following:
      1. **Tên cocktail** (a creative name)
      2. **Nguyên liệu & Định lượng** (full ingredients list with exact measures)
      3. **Công thức pha chế** (step-by-step mixing instructions with technique details: shake, stir, build, etc.)
      4. **Trang trí & Garnish** (detailed decoration guide: rim salt/sugar, garnish type and placement, ice type, glassware)
      5. **Ý nghĩa & Câu chuyện** (the story, meaning, or creative inspiration behind this cocktail)
      6. CRITICAL - GENERATIVE ART HACK: You MUST include an image of your creation. Append a Markdown image tag at the end using this exact format:
         `![Cocktail Image](https://image.pollinations.ai/prompt/A%20stunning%20professional%20photography%20of%20a%20cocktail%20with%20[INGREDIENTS]%20in%20a%20[MOOD]%20bar%20setting)`
         Replace [INGREDIENTS] and [MOOD] with URL-encoded descriptions of your drink.
    </rule>
    <rule>Personalization: If a User Taste Profile is provided, strictly adhere to their likes and dislikes.</rule>
  </rules>
</system_prompt>
"""

QA_AGENT_INSTRUCTION = """
<system_prompt>
  <agent>
    <name>Quality Assurance Evaluator</name>
    <organization>AI Lounge</organization>
    <persona>Strict, observant, logical fact-checker.</persona>
  </agent>
  <objective>
    Evaluate the proposed response from the main AI. Ensure it does not hallucinate fake bars, invent unsafe/toxic cocktail recipes, or misinterpret the user's intent.
  </objective>
  <rules>
    <rule>If the response recommends a Bar, verify if the bar is realistic or if the AI admits it couldn't find it. If it hallucinated a fake bar, respond with "REJECT: Hallucinated Bar".</rule>
    <rule>If the response provides a recipe with dangerous or toxic ingredients (e.g. bleach, raw unsafe items), respond with "REJECT: Unsafe recipe".</rule>
    <rule>If the response is perfectly fine, safe, and logical, simply respond with "APPROVE".</rule>
  </rules>
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

    def _extract_taste_profile(self, chat_history: list) -> str:
        """
        Analyzes chat history to extract a Long-Term Memory taste profile.
        Returns a string summarizing the user's likes/dislikes.
        """
        # Very simple heuristic extractor to save cost, or we can just send the last 5 turns to an LLM.
        # For simplicity and speed, we look for explicit keywords in user messages.
        likes = []
        dislikes = []
        
        for turn in chat_history:
            if turn.get("role") == "user":
                text = str(turn.get("parts", [""])[0]).lower()
                if "thích" in text or "like" in text or "love" in text:
                    # Simple heuristic: grab the next word or phrase
                    likes.append(text)
                if "ghét" in text or "không thích" in text or "hate" in text or "dislike" in text or "dị ứng" in text:
                    dislikes.append(text)
                    
        profile = ""
        if likes or dislikes:
            profile = "USER TASTE PROFILE: "
            if likes:
                profile += f"User mentioned liking things related to: {' | '.join(likes[-3:])}. "
            if dislikes:
                profile += f"User mentioned DISLIKING things related to: {' | '.join(dislikes[-3:])}. AVOID THESE."
        return profile

    def _detect_intent(self, user_message: str) -> str:
        """
        Lightweight fast semantic router to determine user intent.
        Returns one of: VENUE_SEARCH, MIXOLOGY_RECIPE, GENERAL_CHAT
        """
        # A simple keyword-based heuristic or a fast LLM call could be used here.
        # For cost optimization and speed, we use a robust heuristic first.
        msg = user_message.lower()
        venue_keywords = ["where", "quán", "bar", "pub", "lounge", "địa điểm", "chơi", "hẹn hò", "place", "location", "go out"]
        recipe_keywords = ["how to", "make", "recipe", "cách pha", "công thức", "nguyên liệu", "ingredient", "mix", "substitute", "thay thế", "abv"]
        
        if any(kw in msg for kw in venue_keywords):
            return "VENUE_SEARCH"
        elif any(kw in msg for kw in recipe_keywords):
            return "MIXOLOGY_RECIPE"
        else:
            return "GENERAL_CHAT"

    def run_chat(self, user_message: str, chat_history: list, role: str = None) -> dict:
        """
        Routes the chat turn to the active LLM provider.
        The 'role' parameter is ignored in V2. Intent is auto-detected.
        """
        # 1. Semantic Routing
        intent = self._detect_intent(user_message)
        print(f"[Semantic Router] Detected Intent: {intent}")
        
        # Override role based on intent for backward compatibility internally
        role = "bartender" if intent == "MIXOLOGY_RECIPE" else "guest"
        
        # 2. Extract Taste Profile
        taste_profile = self._extract_taste_profile(chat_history)
        if taste_profile:
            print(f"[Memory Agent] Extracted Profile: {taste_profile}")
            user_message = f"{taste_profile}\n\nUSER REQUEST: {user_message}"
            
        # Determine active provider
        if self.provider == "gemini":
            result = self.run_chat_gemini(user_message, chat_history, role)
        else:
            # OpenAI, OpenRouter, or Custom
            result = self.run_chat_openai_compatible(user_message, chat_history, role)
            
        # Multi-Agent Evaluation Loop
        is_approved, feedback = self._evaluate_response(user_message, result["message"])
        if not is_approved:
            print(f"[QA Agent] Response rejected. Reason: {feedback}")
            # Self-reflection: send the rejection back to the main agent to regenerate
            reflection_msg = f"SYSTEM QA EVALUATION FAILED: {feedback}. Please rewrite your response to fix this issue."
            # We recursively call run_chat but append the failure to the history
            temp_history = result["chat_history"]
            temp_history.append({"role": "user", "parts": [reflection_msg]})
            
            if self.provider == "gemini":
                result = self.run_chat_gemini("I have noted the feedback. Let me try again.", temp_history, role)
            else:
                result = self.run_chat_openai_compatible("I have noted the feedback. Let me try again.", temp_history, role)
                
            # Strip the temporary reflection loop from the final history so the user doesn't see the internal QA dialogue
            result["chat_history"] = chat_history + [
                {"role": "user", "parts": [user_message]},
                {"role": "model", "parts": [result["message"]]}
            ]
            
        return result

    def _evaluate_response(self, user_query: str, agent_response: str) -> tuple[bool, str]:
        """
        QA Agent evaluates the output. Returns (is_approved, feedback_string)
        """
        prompt = f"User asked: '{user_query}'\nAgent responded: '{agent_response}'\n\nBased on your system instructions, output 'APPROVE' if it's safe and realistic. Otherwise output 'REJECT: <reason>'."
        
        try:
            import requests
            if self.provider == "gemini":
                model = genai.GenerativeModel(model_name=Config.GEMINI_MODEL, system_instruction=QA_AGENT_INSTRUCTION)
                response = model.generate_content(prompt)
                res_text = response.text.strip()
            else:
                # OpenRouter / OpenAI / Custom
                api_key = Config.CUSTOM_API_KEY if self.provider == "custom" else Config.OPENROUTER_API_KEY if self.provider == "openrouter" else Config.OPENAI_API_KEY
                url = Config.CUSTOM_API_BASE if self.provider == "custom" else "https://openrouter.ai/api/v1/chat/completions" if self.provider == "openrouter" else "https://api.openai.com/v1/chat/completions"
                model_name = Config.CUSTOM_MODEL if self.provider == "custom" else Config.OPENROUTER_MODEL if self.provider == "openrouter" else Config.OPENAI_MODEL
                
                if self.provider == "custom" and not url.endswith("/chat/completions"):
                    url = url.rstrip("/") + "/chat/completions"
                    
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": QA_AGENT_INSTRUCTION},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.0,
                    "max_tokens": 100
                }
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    res_data = resp.json()
                    res_text = res_data["choices"][0]["message"]["content"].strip()
                else:
                    res_text = "APPROVE" # Fallback if QA fails
                    
            if res_text.startswith("REJECT"):
                return False, res_text.replace("REJECT:", "").strip()
            return True, ""
            
        except Exception as e:
            print(f"[QA Agent] Error evaluating response: {e}")
            return True, "" # Failsafe approve
            
    def _get_role_tools(self, role: str) -> list:
        if role == "bartender":
            return [
                "db_search_cocktails",
                "generate_custom_recipe",
                "substitute_ingredient",
                "calculate_abv",
                "calculate_cost_and_shopping_list"
            ]
        else:
            return [
                "db_search_cocktails",
                "db_search_bars",
                "recommend_food_pairing"
            ]

    def run_chat_gemini(self, user_message: str, chat_history: list, role: str) -> dict:
        """
        Executes a turn using Gemini native SDK with dynamic tool subsets.
        """
        try:
            active_tool_names = self._get_role_tools(role)
            print(f"[Tool Router] Role: {role} -> Assigned {len(active_tool_names)} tools")
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
            active_tool_names = self._get_role_tools(role)
            print(f"[Tool Router] Role: {role} -> Assigned {len(active_tool_names)} tools")
            
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
                
                # Free OpenRouter accounts have a strict limit on requested tokens.
                # If we don't specify max_tokens, it defaults to the model's max context (up to 2M) and fails.
                payload["max_tokens"] = 4096
                    
                if openai_tools:
                    payload["tools"] = openai_tools
                    payload["tool_choice"] = "auto"
                
                resp = requests.post(url, headers=headers, json=payload, timeout=90)
                if resp.status_code != 200:
                    raise Exception(f"API error from '{self.provider}' ({resp.status_code}): {resp.text}")
                    
                try:
                    res_data = resp.json()
                except ValueError:
                    import json
                    # 9router sometimes returns trailing data or multiple lines
                    raw = resp.text.strip()
                    try:
                        # Extract the first valid JSON string from potentially broken output
                        res_data = json.loads(raw.split('\n')[0])
                    except Exception:
                        # Fallback for extra data
                        import re
                        match = re.search(r'^(\{.*\})', raw, re.DOTALL)
                        if match:
                            res_data = json.loads(match.group(1))
                        else:
                            raise Exception(f"Failed to parse JSON response: {raw[:200]}")
                            
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
