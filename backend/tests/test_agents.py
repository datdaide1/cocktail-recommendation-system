import pytest
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.graph import graph

@pytest.mark.asyncio
async def test_router_b2c_classification():
    # Query with B2C keywords
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
    assert result["tool_called"] is False
    
    # Check that a response was appended
    assert len(result["messages"]) > 1
    assert isinstance(result["messages"][-1], AIMessage)

@pytest.mark.asyncio
async def test_router_b2b_classification():
    # Query with B2B keywords and ingredient pricing/margin
    state = {
        "messages": [HumanMessage(content="What is the pricing and cost of 50ml Absolut Vodka and 150ml Water for menu planning?")],
        "intent": None,
        "customer_age": None,
        "allergies": [],
        "safety_status": "safe",
        "tool_called": False
    }
    result = await graph.ainvoke(state)
    assert result["intent"] == "b2b"
    assert result["tool_called"] is True
    
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    assert "B2B Pricing and ABV Analysis" in last_msg.content
    assert "Total Cost: 25000.0" in last_msg.content
    assert "ABV: 10.0" in last_msg.content

@pytest.mark.asyncio
async def test_b2b_tool_called_state():
    # Even with metadata-based B2B intent, tool should be called and tracked
    msg = HumanMessage(content="Analyze cost breakdown for ingredients.")
    msg.additional_kwargs["metadata"] = {"intent": "b2b"}
    state = {
        "messages": [msg],
        "intent": None,
        "customer_age": None,
        "allergies": [],
        "safety_status": "safe",
        "tool_called": False
    }
    result = await graph.ainvoke(state)
    assert result["intent"] == "b2b"
    assert result["tool_called"] is True
    assert "B2B Pricing and ABV Analysis" in result["messages"][-1].content

@pytest.mark.asyncio
async def test_underage_safety_redirect():
    # Age passed in text query
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
    
    last_msg = result["messages"][-1]
    assert "under 18" in last_msg.content.lower() or "cannot recommend alcoholic" in last_msg.content.lower()
    assert "Non-alcoholic Gin and Tonic (Mocktail)" in last_msg.content

@pytest.mark.asyncio
async def test_underage_safety_metadata():
    # Age passed in metadata
    msg = HumanMessage(content="Recommend a Gin and Tonic.")
    msg.additional_kwargs["metadata"] = {"age": 17}
    state = {
        "messages": [msg],
        "intent": None,
        "customer_age": None,
        "allergies": [],
        "safety_status": "safe",
        "tool_called": False
    }
    result = await graph.ainvoke(state)
    assert result["customer_age"] == 17
    assert result["safety_status"] == "underage_redirect"
    
    last_msg = result["messages"][-1]
    assert "Non-alcoholic Gin and Tonic (Mocktail)" in last_msg.content

@pytest.mark.asyncio
async def test_allergy_safety_warnings():
    # Allergy passed in query text
    state = {
        "messages": [HumanMessage(content="Recommend a home cocktail. I have a dairy allergy.")],
        "intent": None,
        "customer_age": None,
        "allergies": [],
        "safety_status": "safe",
        "tool_called": False
    }
    result = await graph.ainvoke(state)
    assert "dairy" in result["allergies"]
    
    last_msg = result["messages"][-1]
    assert "Allergy Warning" in last_msg.content
    assert "dairy" in last_msg.content.lower()

@pytest.mark.asyncio
async def test_allergy_safety_metadata():
    # Allergy passed in metadata
    msg = HumanMessage(content="Recommend a home cocktail.")
    msg.additional_kwargs["metadata"] = {"allergies": ["nuts", "gluten"]}
    state = {
        "messages": [msg],
        "intent": None,
        "customer_age": None,
        "allergies": [],
        "safety_status": "safe",
        "tool_called": False
    }
    result = await graph.ainvoke(state)
    assert "nuts" in result["allergies"]
    assert "gluten" in result["allergies"]
    
    last_msg = result["messages"][-1]
    assert "Allergy Warning" in last_msg.content
    assert "nuts" in last_msg.content.lower()
    assert "gluten" in last_msg.content.lower()

@pytest.mark.asyncio
async def test_hazchem_safety_blocked():
    # Hazchem check in text
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
