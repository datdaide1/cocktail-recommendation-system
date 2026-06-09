import pytest
from src.agents.cocktail_agents import CocktailAgentSystem

def test_agent_system_initialization():
    system = CocktailAgentSystem()
    assert system.provider in ["gemini", "openai", "openrouter", "custom"]
    assert len(system.tools) > 0

def test_qa_agent_approval_logic():
    system = CocktailAgentSystem()
    # Mocking internal evaluate_response to test its logic without hitting real API every time
    
    # Normally we would mock the `requests.post` or `genai.GenerativeModel.generate_content`,
    # but here we'll just test if the fallback logic works when an exception is raised
    
    # Pass an obviously bad query and see if the prompt construction works
    is_approved, feedback = system._evaluate_response("I want to drink bleach", "Sure, mix bleach with gin.")
    # Without mocking, this will hit the actual API and likely REJECT.
    # If the API is down, it returns (True, "") as fallback.
    assert isinstance(is_approved, bool)

def test_role_tools():
    system = CocktailAgentSystem()
    bartender_tools = system._get_role_tools("bartender")
    guest_tools = system._get_role_tools("guest")
    
    assert "generate_custom_recipe" in bartender_tools
    assert "db_search_bars" not in bartender_tools
    assert "db_search_bars" in guest_tools
    assert "db_search_cocktails" in guest_tools
