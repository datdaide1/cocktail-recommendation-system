import json

def calculate_abv(ingredients_with_ml: str) -> str:
    """
    Calculate the estimated Alcohol By Volume (ABV) percentage of a cocktail based on volumes and ingredient ABVs.
    
    Args:
        ingredients_with_ml: JSON string of ingredients and their volumes, e.g.:
          '[{"name": "Gin", "abv": 40, "volume_ml": 45}, {"name": "Lime Juice", "abv": 0, "volume_ml": 15}]'
          
    Returns:
        JSON string containing the total volume, estimated ABV percentage, and description
    """
    try:
        items = json.loads(ingredients_with_ml)
    except Exception as e:
        return json.dumps({"error": f"JSON parsing error: {e}"})
        
    total_volume = 0.0
    total_alcohol = 0.0
    
    for item in items:
        vol = float(item.get("volume_ml", 0.0))
        abv = float(item.get("abv", 0.0))
        
        total_volume += vol
        total_alcohol += (vol * abv / 100.0)
        
    if total_volume == 0:
        return json.dumps({"error": "Total volume must be greater than 0ml."})
        
    final_abv = (total_alcohol / total_volume) * 100.0
    
    if final_abv == 0:
        abv_category = "Mocktail (Non-alcoholic)"
    elif final_abv < 10:
        abv_category = "Low ABV"
    elif final_abv < 20:
        abv_category = "Medium ABV"
    else:
        abv_category = "Strong ABV"
        
    result = {
        "total_volume_ml": round(total_volume, 1),
        "estimated_abv": round(final_abv, 1),
        "abv_category": abv_category,
        "description": f"The cocktail has a total volume of {round(total_volume, 1)}ml with an estimated ABV of {round(final_abv, 1)}% ({abv_category})."
    }
    
    return json.dumps(result, ensure_ascii=False)

def calculate_cost_and_shopping_list(ingredients_list: str) -> str:
    """
    Estimates the purchasing cost of ingredients in VND for making cocktails and generates a structured shopping list.
    
    Args:
        ingredients_list: Comma-separated list of ingredients needed, e.g. 'gin, lime, mint, tonic, sugar'
        
    Returns:
        JSON string with itemized retail prices in Vietnam, estimated total cost, and shopping suggestions.
    """
    # Sample price dictionary in VND for retail items in Vietnam supermarkets / online liquor stores
    price_catalog = {
        "gin": {"item": "Dry Gin Bottle (700ml)", "price_vnd": 350000},
        "vodka": {"item": "Vodka Bottle (700ml)", "price_vnd": 220000},
        "rum": {"item": "White Rum Bottle (700ml)", "price_vnd": 260000},
        "tequila": {"item": "Tequila Bottle (750ml)", "price_vnd": 450000},
        "whiskey": {"item": "Bourbon Whiskey (700ml)", "price_vnd": 550000},
        "bourbon": {"item": "Bourbon Whiskey (700ml)", "price_vnd": 550000},
        "vermouth": {"item": "Sweet/Dry Vermouth (750ml)", "price_vnd": 320000},
        "cointreau": {"item": "Cointreau Orange Liqueur (700ml)", "price_vnd": 580000},
        "triple sec": {"item": "Triple Sec Liqueur (700ml)", "price_vnd": 280000},
        "campari": {"item": "Campari Bitter (750ml)", "price_vnd": 480000},
        "aperol": {"item": "Aperol Liqueur (700ml)", "price_vnd": 380000},
        "tonic": {"item": "Tonic Water (Pack of 6 cans)", "price_vnd": 540000 // 6 * 6}, # ~54k pack
        "soda": {"item": "Soda Water (Pack of 6 cans)", "price_vnd": 48000},
        "lime": {"item": "Fresh Limes (1kg)", "price_vnd": 25000},
        "lemon": {"item": "Fresh Lemons (500g)", "price_vnd": 35000},
        "mint": {"item": "Fresh Mint Leaves (100g)", "price_vnd": 12000},
        "sugar": {"item": "White Granulated Sugar (1kg)", "price_vnd": 22000},
        "bitters": {"item": "Angostura Aromatic Bitters (200ml)", "price_vnd": 650000},
        "angostura": {"item": "Angostura Aromatic Bitters (200ml)", "price_vnd": 650000},
        "grenadine": {"item": "Grenadine Syrup (750ml)", "price_vnd": 120000},
        "syrup": {"item": "Monin Simple Syrup (700ml)", "price_vnd": 180000}
    }
    
    query_items = [i.strip().lower() for i in ingredients_list.split(',') if i.strip()]
    
    shopping_items = []
    total_cost = 0
    
    for qi in query_items:
        matched = False
        # Match against our catalog keys
        for key, details in price_catalog.items():
            if key in qi or qi in key:
                shopping_items.append({
                    "requested": qi,
                    "store_item": details["item"],
                    "estimated_cost_vnd": details["price_vnd"]
                })
                total_cost += details["price_vnd"]
                matched = True
                break
        
        if not matched:
            # Add general item estimation
            shopping_items.append({
                "requested": qi,
                "store_item": f"Specialty Ingredient: {qi.title()}",
                "estimated_cost_vnd": 45000 # default fallback estimate
            })
            total_cost += 45000
            
    result = {
        "shopping_list": shopping_items,
        "estimated_total_cost_vnd": total_cost,
        "currency": "VND",
        "notes": "Prices are estimated average retail prices in local Vietnamese supermarkets (Annam Gourmet, WinMart) or online shops."
    }
    
    return json.dumps(result, ensure_ascii=False)
