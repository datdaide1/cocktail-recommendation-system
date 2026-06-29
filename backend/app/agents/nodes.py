import re
import logging
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, BaseMessage
from app.agents.state import AgentState
from app.tools.cost_abv_calculator import calculate_cost_and_abv

logger = logging.getLogger(__name__)

def capitalize_drink(name: str) -> str:
    """Capitalize every word of a drink name except 'and'."""
    return " ".join(w.title() if w.lower() != "and" else "and" for w in name.split())


def parse_ingredients_from_query(query: str) -> List[Dict[str, Any]]:
    """Helper to parse ingredients and volumes from user query."""
    clean_query = query.replace("?", " ").replace("\n", " ")
    # Split query by common delimiters: comma, semicolon, "and", plus, period
    clauses = re.split(r"\b(?:and)\b|[\,\;\.\+]+", clean_query, flags=re.IGNORECASE)
    ingredients = []
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        # Pattern 1: <volume> ml <name>
        m1 = re.search(r"(\d+(?:\.\d+)?)\s*ml\s*(?:of\s+)?([A-Za-z0-9\s\-']+)", clause, re.IGNORECASE)
        if m1:
            vol = float(m1.group(1))
            name = m1.group(2).strip()
            name = re.sub(r"^[^\w]+", "", name)
            name = re.sub(r"[^\w]+$", "", name)
            name = re.sub(r"^(?:of|with|add|plus|and)\s+", "", name, flags=re.IGNORECASE).strip()
            if name:
                ingredients.append({"name": name, "volume_ml": vol})
            continue
        # Pattern 2: <name> <volume> ml
        m2 = re.search(r"([A-Za-z0-9\s\-'\u00C0-\u017F]+?)\s*(\d+(?:\.\d+)?)\s*ml", clause, re.IGNORECASE)
        if m2:
            name = m2.group(1).strip()
            vol = float(m2.group(2))
            name = re.sub(r"^[^\w]+", "", name)
            name = re.sub(r"[^\w]+$", "", name)
            name = re.sub(r"^(?:of|with|add|plus|and)\s+", "", name, flags=re.IGNORECASE).strip()
            if name:
                ingredients.append({"name": name, "volume_ml": vol})
            continue
    return ingredients

async def router_node(state: AgentState) -> dict:
    """Router node to parse input query, detect age/allergies/intent/hazchem."""
    last_message = state["messages"][-1] if state.get("messages") else None
    content = last_message.content if last_message else ""

    # Parse metadata if present
    metadata = {}
    if last_message and hasattr(last_message, "additional_kwargs"):
        metadata = last_message.additional_kwargs.get("metadata") or last_message.additional_kwargs or {}

    # 1. Parse Customer Age
    age = state.get("customer_age")
    if age is None:
        if isinstance(metadata, dict):
            if "age" in metadata:
                age = int(metadata["age"])
            elif "customer_age" in metadata:
                age = int(metadata["customer_age"])
        if age is None:
            age_patterns = [
                r"\b(?:i\s+am|i'm)\s*(\d+)(?:\s*years?\s*old)?\b",
                r"\bage\s*(?:is|:)?\s*(\d+)\b",
                r"\b(\d+)\s*years?\s*old\b",
                r"\b(\d+)\s*years?\s*of\s*age\b"
            ]
            for pattern in age_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    age = int(match.group(1))
                    break

    # 2. Parse Allergies
    allergies = list(state.get("allergies") or [])
    if isinstance(metadata, dict) and "allergies" in metadata:
        meta_allergies = metadata["allergies"]
        if isinstance(meta_allergies, str):
            if meta_allergies not in allergies:
                allergies.append(meta_allergies)
        elif isinstance(meta_allergies, list):
            for a in meta_allergies:
                if a not in allergies:
                    allergies.append(a)

    known_allergens = ["nuts", "peanut", "dairy", "gluten", "soy", "egg", "milk", "cream", "almond"]
    for allergen in known_allergens:
        if re.search(r"\b" + re.escape(allergen) + r"s?\b", content, re.IGNORECASE):
            if allergen not in allergies:
                allergies.append(allergen)

    allergy_patterns = [
        r"\ballergic\s+to\s+([A-Za-z0-9\s\-]+)",
        r"\ballergy\s+to\s+([A-Za-z0-9\s\-]+)",
        r"\b([A-Za-z0-9\s\-]+)\s+allergy\b",
        r"\bno\s+([A-Za-z0-9\s\-]+)\b"
    ]
    for pattern in allergy_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            allergen = match.group(1).strip().lower()
            allergen = re.sub(r"^(?:a|an|some)\s+", "", allergen)
            allergen = re.sub(r"[^\w\s\-]", "", allergen).strip()
            if allergen and allergen not in allergies:
                allergies.append(allergen)

    # 3. Detect Hazchem safety status
    safety_status = state.get("safety_status", "safe")
    toxic_substances = [
        "rubbing alcohol", "isopropyl", "bleach", "methanol", "cyanide", "battery acid",
        "ethylene glycol", "household chemical", "poison", "toxic", "drain cleaner",
        "ammonia", "acetone", "kerosene", "gasoline", "motor oil", "antifreeze",
        "arsenic", "strychnine", "mercury", "lead", "pesticide", "herbicide",
        "rat poison", "detergent", "soap", "window cleaner"
    ]
    is_hazchem = False
    for substance in toxic_substances:
        if re.search(r"\b" + re.escape(substance) + r"s?\b", content, re.IGNORECASE):
            is_hazchem = True
            break

    if is_hazchem:
        safety_status = "hazchem_blocked"
    elif age is not None and age < 18:
        safety_status = "underage_redirect"
    elif safety_status not in ["hazchem_blocked", "underage_redirect"]:
        safety_status = "safe"

    # 4. Classify Intent
    intent = state.get("intent")
    if not intent:
        if isinstance(metadata, dict) and "intent" in metadata:
            intent = metadata["intent"]
        if not intent:
            b2b_keywords = [
                "pricing", "menu planning", "bar profit margin", "profit", "margin", "cost", "breakdown",
                "calculate cost", "abv calculation", "bulk", "business", "wholesale", "commercial",
                "price per ml", "liquor prices", "profitability", "cost of"
            ]
            b2c_keywords = [
                "home cocktail", "vibe", "recommendation", "recipe", "how to make", "make at home",
                "sweet", "sour", "fruity", "glass", "garnish", "party", "drink", "mixologist", "mocktail"
            ]
            b2b_score = sum(1 for kw in b2b_keywords if kw in content.lower())
            b2c_score = sum(1 for kw in b2c_keywords if kw in content.lower())

            parsed = parse_ingredients_from_query(content)
            if parsed and ("cost" in content.lower() or "abv" in content.lower() or "price" in content.lower() or "calculate" in content.lower()):
                b2b_score += 3

            if b2b_score > b2c_score:
                intent = "b2b"
            else:
                intent = "b2c"

    return {
        "customer_age": age,
        "allergies": allergies,
        "intent": intent,
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
    """B2C node to handle consumer queries, age restrictions, and allergy warnings."""
    last_message = state["messages"][-1] if state.get("messages") else None
    content = last_message.content if last_message else ""

    if state.get("safety_status") == "hazchem_blocked":
        msg = AIMessage(content="I cannot help you with hazardous chemicals. That is unsafe.")
        return {"messages": [msg]}

    is_underage = (state.get("safety_status") == "underage_redirect") or (state.get("customer_age") is not None and state["customer_age"] < 18)
    allergies = state.get("allergies") or []

    # Find if user requested a specific drink
    requested_drink = None
    common_drinks = ["gin and tonic", "margarita", "martini", "mojito", "daquiri", "whiskey sour", "pina colada"]
    for drink in common_drinks:
        if drink in content.lower():
            requested_drink = drink
            break

    if is_underage:
        if requested_drink:
            drink_name = f"Non-alcoholic {capitalize_drink(requested_drink)} (Mocktail)"
            response_text = (
                f"Since you are under 18, I cannot recommend alcoholic drinks. "
                f"Here is a {drink_name} instead.\n"
                f"Ingredients: Soda water, lime juice, non-alcoholic botanicals syrup."
            )
        else:
            response_text = (
                "Since you are under 18, I cannot recommend alcoholic drinks. "
                "Here is a Virgin Mojito (Mocktail) instead.\n"
                f"Ingredients: Fresh mint leaves, lime juice, simple syrup, soda water."
            )
    else:
        if requested_drink:
            response_text = (
                f"Here is a recipe for a classic {capitalize_drink(requested_drink)}.\n"
                f"Ingredients: 50ml Gin, 150ml Tonic water, lime wedge."
            )
        else:
            response_text = (
                "Here is a recommended cocktail: Gin and Tonic.\n"
                f"Ingredients: 50ml Gin, 150ml Tonic water, lime wedge."
            )

    allergy_warnings = []
    if allergies:
        for allergy in allergies:
            allergy_warnings.append(f"Allergy Warning: Please ensure no {allergy} is used in this recipe.")

    if allergy_warnings:
        response_text += "\n\n" + "\n".join(allergy_warnings)

    return {"messages": [AIMessage(content=response_text)]}

async def b2b_bartender_node(state: AgentState) -> dict:
    """B2B node for cost and ABV calculation."""
    last_message = state["messages"][-1] if state.get("messages") else None
    content = last_message.content if last_message else ""

    # Parse ingredients
    ingredients = parse_ingredients_from_query(content)
    if not ingredients:
        # Fallback to standard B2B setup if query didn't specify ingredients
        ingredients = [
            {"name": "Absolut Vodka", "volume_ml": 50},
            {"name": "Water", "volume_ml": 150}
        ]

    # Call cost and ABV calculator tool
    calc_result = await calculate_cost_and_abv(ingredients)

    total_cost = calc_result.get("total_cost_vnd", 0.0)
    abv = calc_result.get("abv", 0.0)
    breakdown = calc_result.get("breakdown", [])

    breakdown_lines = []
    for item in breakdown:
        breakdown_lines.append(f"- {item['name']}: {item['volume_ml']}ml, Cost: {item['cost']} VND, ABV: {item['abv']}%")

    response_text = (
        f"B2B Pricing and ABV Analysis:\n"
        f"Total Cost: {total_cost} VND\n"
        f"ABV: {abv}%\n"
        f"Cost Breakdown:\n" + "\n".join(breakdown_lines)
    )

    return {
        "messages": [AIMessage(content=response_text)],
        "tool_called": True
    }
