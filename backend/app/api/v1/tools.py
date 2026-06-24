from fastapi import APIRouter
from app.schemas.chat import ToolCalculateCostRequest
from app.agents.tools.calculators import calculate_cost_and_abv

router = APIRouter()

@router.post("/calculate_cost")
async def calculate_cost(req: ToolCalculateCostRequest):
    result = calculate_cost_and_abv(req.recipe)
    return result
