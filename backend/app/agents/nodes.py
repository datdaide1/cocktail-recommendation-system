import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from app.agents.state import AgentState
from app.tools.cost_abv_calculator import calculate_cost_and_abv
from app.core.config import settings
from pydantic import BaseModel, Field
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Initialize LLM via OpenRouter
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENAI_API_BASE,
    temperature=0.0
)

class RouterSchema(BaseModel):
    intent: str = Field(description="Must be 'b2b' if user asks for pricing, margins, or cost calculation. Must be 'b2c' if user asks for recipes, vibes, or cocktail recommendations.")
    customer_age: int = Field(description="The age of the customer if mentioned, else -1.", default=-1)
    allergies: str = Field(description="A comma-separated string of allergies mentioned by the user, or empty string if none.", default="")
    safety_status: str = Field(description="Must be 'hazchem_blocked' if they ask for poisons/chemicals. Must be 'underage_redirect' if they are under 18 and ask for alcohol. Otherwise 'safe'.", default="safe")

async def router_node(state: AgentState) -> dict:
    """Router node to parse input query using LLM structured output."""
    last_message = state["messages"][-1]
    
    system_prompt = (
        "You are a routing agent for a cocktail recommendation system.\n"
        "Analyze the user's query and extract their intent, age, allergies, and safety status.\n"
        "Intent must be 'b2b' for business/cost inquiries and 'b2c' for consumers.\n"
        "If they mention toxic chemicals/poisons, set safety_status to 'hazchem_blocked'.\n"
        "If they are under 18 and asking for alcohol, set safety_status to 'underage_redirect'."
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        last_message
    ]
    
    # Use with_structured_output to parse the metadata
    structured_llm = llm.with_structured_output(RouterSchema)
    
    try:
        parsed_data = await structured_llm.ainvoke(messages)
    except Exception as e:
        logger.error(f"Router LLM Error: {e}")
        parsed_data = {"intent": "b2c", "customer_age": None, "allergies": [], "safety_status": "safe"}
        
    if isinstance(parsed_data, dict):
        age = parsed_data.get("customer_age", -1)
        allergies_str = parsed_data.get("allergies", "")
        safety_status = parsed_data.get("safety_status", "safe")
        intent = parsed_data.get("intent", "b2c")
    else:
        age = getattr(parsed_data, "customer_age", -1)
        allergies_str = getattr(parsed_data, "allergies", "")
        safety_status = getattr(parsed_data, "safety_status", "safe")
        intent = getattr(parsed_data, "intent", "b2c")
        
    return {
        "intent": intent,
        "customer_age": None if age == -1 else age,
        "allergies": [a.strip() for a in allergies_str.split(",")] if allergies_str else [],
        "safety_status": safety_status
    }

def router_edge(state: AgentState) -> str:
    """Conditional edge decision maker based on intent and safety."""
    if state["safety_status"] == "hazchem_blocked":
        return "hazchem_block_node"
    elif state["intent"] == "b2b":
        return "b2b_bartender_node"
    else:
        return "b2c_mixologist_node"

async def hazchem_block_node(state: AgentState) -> dict:
    """Immediate block for hazardous chemicals."""
    msg = AIMessage(content="I cannot help you with hazardous chemicals. That is unsafe.")
    return {
        "messages": [msg],
        "safety_status": "hazchem_blocked"
    }

async def b2c_mixologist_node(state: AgentState) -> dict:
    """B2C node to handle consumer queries, age restrictions, and allergy warnings using LLM."""
    last_message = state["messages"][-1]
    
    system_prompt = (
        "You are an expert Mixologist for consumers (B2C).\n"
        "Provide friendly, expert recommendations, recipes, and vibes based on the user's request.\n"
    )
    
    # Handle safety overrides
    if state.get("safety_status") == "underage_redirect" or (state.get("customer_age") is not None and state["customer_age"] < 18):
        system_prompt += (
            "CRITICAL: The user is underage. You MUST ONLY recommend non-alcoholic mocktails or water. "
            "Politely inform them you cannot recommend alcohol and provide a mocktail recipe."
        )
        
    if state.get("allergies"):
        allergies_str = ", ".join(state["allergies"])
        system_prompt += (
            f"\nCRITICAL ALLERGY WARNING: The user is allergic to: {allergies_str}. "
            "You MUST ensure the recommended drinks do not contain these ingredients."
        )
        
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    response = await llm.ainvoke(messages)
    return {"messages": [response]}

@tool
async def calculate_cost_tool(ingredients: List[Dict[str, Any]]) -> str:
    """Calculate the total cost and ABV of a cocktail given its ingredients.
    The 'ingredients' parameter must be a list of dictionaries, each with 'name' (string) and 'volume_ml' (float).
    """
    res = await calculate_cost_and_abv(ingredients)
    return json.dumps(res, indent=2)

async def b2b_bartender_node(state: AgentState) -> dict:
    """B2B node for cost and ABV calculation utilizing LLM tool binding."""
    
    system_prompt = (
        "You are a Master Bartender for business inquiries (B2B).\n"
        "Your main job is to help bar owners calculate costs, ABV, and profit margins.\n"
        "You MUST use the calculate_cost_tool to calculate the cost and ABV of the drink the user asks for.\n"
        "If the user doesn't specify exact volumes, assume standard volumes (e.g., 45ml or 50ml for base spirits, 15ml for syrups, 150ml for mixers).\n"
        "Always present a clear cost breakdown."
    )
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    # Bind tools to the LLM
    b2b_llm = llm.bind_tools([calculate_cost_tool])
    
    response = await b2b_llm.ainvoke(messages)
    
    return {
        "messages": [response],
        "tool_called": bool(response.tool_calls) if hasattr(response, 'tool_calls') else False
    }
