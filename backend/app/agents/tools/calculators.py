from typing import List, Dict, Any

def calculate_cost_and_abv(recipe: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Mock calculation logic connecting to PostgreSQL / Local JSON
    total_cost = 0
    total_vol = 0
    for item in recipe:
        amount = item.get("amount_ml", 0)
        total_vol += amount
        total_cost += amount * 500  # mock 500 vnd/ml
    
    return {
        "total_cost_vnd": total_cost,
        "total_volume_ml": total_vol,
        "estimated_abv": 20.0
    }
