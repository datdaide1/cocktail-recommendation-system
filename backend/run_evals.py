import os
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
import braintrust
from autoevals import Factuality, AnswerRelevancy, ContextRelevancy
from langchain_core.messages import HumanMessage

load_dotenv()

from app.agents.graph import graph
from app.agents.state import AgentState

def tool_calling_scorer(output: Dict[str, Any], **kwargs):
    """
    Custom scorer to validate B2B Tool Calling.
    If the intent was B2B, check if the tool was called.
    """
    intent = output.get("intent")
    tool_called = output.get("tool_called", False)
    
    if intent == "b2b":
        score = 1.0 if tool_called else 0.0
        return braintrust.Score(
            name="ToolCallingValidation",
            score=score,
            metadata={"intent": intent, "tool_called": tool_called}
        )
    else:
        # If not B2B, tool calling is not required, we can ignore or return 1.0
        return braintrust.Score(
            name="ToolCallingValidation",
            score=1.0,
            metadata={"intent": intent, "tool_called": tool_called}
        )

async def task_fn(input_data: str) -> Dict[str, Any]:
    """
    The task function that runs the input through our LangGraph pipeline.
    """
    state = AgentState(
        messages=[HumanMessage(content=input_data)],
        intent=None,
        customer_age=None,
        allergies=[],
        safety_status="safe",
        context="",
        tool_called=False
    )
    
    # Run the graph
    result = await graph.ainvoke(state)
    
    # Extract outputs
    last_message = result["messages"][-1].content
    context = result.get("context", "")
    
    return {
        "output": last_message,
        "context": context,
        "intent": result.get("intent"),
        "tool_called": result.get("tool_called", False),
        "safety_status": result.get("safety_status")
    }

async def run_evaluation():
    # Evaluate using braintrust
    # Note: autoevals requires expected, output, and sometimes input/context
    
    await braintrust.EvalAsync(
        "Cocktail-Recommendation-System",
        data=braintrust.init_dataset("Cocktail-Recommendation-System", "Cocktail-Scenarios-Golden"),
        task=task_fn,
        scores=[
            # Factuality (Faithfulness): Is the output grounded in the context?
            lambda input, output, expected, **kwargs: Factuality()(input=input, output=output.get("output"), expected=expected, context=output.get("context", "")),
            
            # Answer Relevancy: Does the output address the input query?
            lambda input, output, **kwargs: AnswerRelevancy()(input=input, output=output.get("output")),
            
            # Context Relevancy: Is the retrieved context relevant to the input query?
            lambda input, output, **kwargs: ContextRelevancy()(input=input, output=output.get("context", "")),
            
            # B2B Tool Calling Validation
            lambda output, **kwargs: tool_calling_scorer(output)
        ]
    )

if __name__ == "__main__":
    asyncio.run(run_evaluation())
