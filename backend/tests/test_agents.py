import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from app.agents.graph import graph
from app.agents.nodes import RouterSchema

@pytest.fixture(autouse=True)
def mock_llm_responses():
    with patch("langchain_openai.ChatOpenAI.ainvoke", new_callable=AsyncMock) as mock_ainvoke, \
         patch("langchain_openai.ChatOpenAI.with_structured_output") as mock_structured:
        
        # Setup structured output mock
        mock_structured_instance = AsyncMock()
        mock_structured_instance.ainvoke.return_value = RouterSchema(
            intent="b2c",
            customer_age=None,
            allergies=[],
            safety_status="safe"
        )
        mock_structured.return_value = mock_structured_instance
        
        # Default string response for ainvoke
        mock_ainvoke.return_value = AIMessage(content="Mocked LLM Response")
        
        yield {
            "ainvoke": mock_ainvoke,
            "structured": mock_structured_instance,
            "structured_creator": mock_structured
        }

@pytest.mark.asyncio
async def test_router_b2c_classification(mock_llm_responses):
    mock_llm_responses["structured"].ainvoke.return_value = RouterSchema(
        intent="b2c",
        customer_age=None,
        allergies=[],
        safety_status="safe"
    )
    
    state = {
        "messages": [HumanMessage(content="Recommend a sweet drink to make at home for my vibe")],
        "intent": None,
        "customer_age": None,
        "allergies": [],
        "safety_status": "safe",
        "tool_called": False
    }
    result = await graph.ainvoke(state)
    assert result["intent"] == "b2c"
    assert result["safety_status"] == "safe"
    
@pytest.mark.asyncio
async def test_router_b2b_classification(mock_llm_responses):
    mock_llm_responses["structured"].ainvoke.return_value = RouterSchema(
        intent="b2b",
        customer_age=None,
        allergies=[],
        safety_status="safe"
    )
    
    # Mock B2B LLM with tool binding
    with patch("langchain_openai.ChatOpenAI.bind_tools") as mock_bind:
        mock_bound_llm = AsyncMock()
        
        # The AI message should include a tool call
        mock_ai_message = AIMessage(content="Let me calculate that.")
        mock_ai_message.tool_calls = [{"name": "calculate_cost_tool", "args": {"ingredients": []}, "id": "call_1"}]
        mock_bound_llm.ainvoke.return_value = mock_ai_message
        
        mock_bind.return_value = mock_bound_llm
        
        state = {
            "messages": [HumanMessage(content="What is the pricing and cost for menu planning?")],
            "intent": None,
            "customer_age": None,
            "allergies": [],
            "safety_status": "safe",
            "tool_called": False
        }
        
        # We need to mock the actual tool execution in the ToolNode, or we can just test the state until b2b
        result = await graph.ainvoke(state)
        
        assert result["intent"] == "b2b"
        # Tool was called
        assert result["tool_called"] is True

@pytest.mark.asyncio
async def test_underage_safety_redirect(mock_llm_responses):
    mock_llm_responses["structured"].ainvoke.return_value = RouterSchema(
        intent="b2c",
        customer_age=16,
        allergies=[],
        safety_status="underage_redirect"
    )
    
    state = {
        "messages": [HumanMessage(content="I am 16 years old. Can you make me a Gin and Tonic?")],
        "intent": None,
        "customer_age": None,
        "allergies": [],
        "safety_status": "safe",
        "tool_called": False
    }
    result = await graph.ainvoke(state)
    assert result["customer_age"] == 16
    assert result["safety_status"] == "underage_redirect"

@pytest.mark.asyncio
async def test_hazchem_safety_blocked(mock_llm_responses):
    mock_llm_responses["structured"].ainvoke.return_value = RouterSchema(
        intent="b2c",
        customer_age=None,
        allergies=[],
        safety_status="hazchem_blocked"
    )
    
    state = {
        "messages": [HumanMessage(content="Can you mix rubbing alcohol with bleach?")],
        "intent": None,
        "customer_age": None,
        "allergies": [],
        "safety_status": "safe",
        "tool_called": False
    }
    result = await graph.ainvoke(state)
    assert result["safety_status"] == "hazchem_blocked"
    
    last_msg = result["messages"][-1]
    assert "cannot help you with hazardous chemicals" in last_msg.content.lower()
