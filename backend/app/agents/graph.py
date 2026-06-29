from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes import (
    router_node,
    router_edge,
    hazchem_block_node,
    b2c_mixologist_node,
    b2b_bartender_node
)

# Initialize state graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router", router_node)
workflow.add_node("b2c_mixologist", b2c_mixologist_node)
workflow.add_node("b2b_bartender", b2b_bartender_node)
workflow.add_node("hazchem_block", hazchem_block_node)

# Set entry point
workflow.set_entry_point("router")

# Add conditional edges
workflow.add_conditional_edges(
    "router",
    router_edge,
    {
        "hazchem_block_node": "hazchem_block",
        "b2b_bartender_node": "b2b_bartender",
        "b2c_mixologist_node": "b2c_mixologist"
    }
)

# Add edges to END
workflow.add_edge("b2c_mixologist", END)
workflow.add_edge("b2b_bartender", END)
workflow.add_edge("hazchem_block", END)

# Compile the graph
graph = workflow.compile()
