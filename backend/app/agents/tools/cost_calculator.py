import json
import os
from app.core.config import settings

def calculate_cost(ingredients: list, quantities: list) -> dict:
    prices_file = os.path.join(settings.DATA_DIR, "liquor_prices.json")
    mixology_file = os.path.join(settings.DATA_DIR, "mixology_data.json")
    
    try:
        with open(prices_file, 'r', encoding='utf-8') as f:
            prices = json.load(f)
        with open(mixology_file, 'r', encoding='utf-8') as f:
            mixology = json.load(f)
    except Exception as e:
        return {"error": str(e)}

    total_cost = 0
    details = []
    
    for ing, qty in zip(ingredients, quantities):
        # find price per ml
        price_per_ml = 0
        found = False
        for p in prices:
            if p.get('name', '').lower() == ing.lower() or ing.lower() in p.get('name', '').lower():
                price_per_ml = p.get('price', 0) / p.get('volume_ml', 1)
                found = True
                break
        
        if not found:
            # fallback mock
            price_per_ml = 500  # 500 VND per ml
            
        cost = price_per_ml * qty
        total_cost += cost
        details.append({"ingredient": ing, "quantity_ml": qty, "cost_vnd": cost})
        
    return {
        "total_cost_vnd": total_cost,
        "details": details
    }
