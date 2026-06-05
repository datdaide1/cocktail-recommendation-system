import json
import pandas as pd
import numpy as np
from pathlib import Path
from src.utils.config import Config

# Helper to load dataframes
def get_cocktails_df():
    try:
        return pd.read_csv(Config.COCKTAILS_PATH).fillna("")
    except Exception as e:
        print(f"Error loading cocktails: {e}")
        return pd.DataFrame()

def get_bars_df():
    try:
        return pd.read_csv(Config.BARS_PATH).fillna("")
    except Exception as e:
        print(f"Error loading bars: {e}")
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# Tool 1: db_search_cocktails
# -----------------------------------------------------------------------------
def db_search_cocktails(ingredients_query: str = "", category: str = "", flavor: str = "", abv: str = "") -> str:
    """
    Search for cocktails in the database based on ingredients, category, flavor profile, or alcohol level.
    
    Args:
        ingredients_query: Comma-separated list of ingredients (e.g., 'gin, lemon')
        category: Cocktail category (e.g., 'Cocktail', 'Shot', 'Ordinary Drink')
        flavor: Target flavor profile (options: 'Chua', 'Ngọt', 'Đắng', 'Thảo mộc', 'Ấm nồng')
        abv: Alcohol level category (options: 'Mocktail (Không cồn)', 'Nhẹ (Low ABV)', 'Vừa (Medium ABV)', 'Mạnh (Strong ABV)')
        
    Returns:
        JSON string containing a list of up to 5 matching cocktails
    """
    df = get_cocktails_df()
    if df.empty:
        return json.dumps({"error": "No cocktail data available."})
        
    results = df.copy()
    
    # 1. Filter by Category
    if category:
        results = results[results['category'].str.lower().str.contains(category.lower())]
        
    # 2. Filter by Flavor
    if flavor:
        results = results[results['flavor_profile'].str.lower().str.contains(flavor.lower())]
        
    # 3. Filter by ABV Category
    if abv:
        results = results[results['abv_category'].str.lower().str.contains(abv.lower())]
        
    # 4. Search by Ingredients
    if ingredients_query:
        query_ingredients = [i.strip().lower() for i in ingredients_query.split(',') if i.strip()]
        
        def calculate_match_score(ingredients_list_str):
            try:
                ing_list = eval(ingredients_list_str)
                ing_list_lower = [str(i).lower() for i in ing_list]
            except:
                ing_list_lower = str(ingredients_list_str).lower()
                
            matches = 0
            for qi in query_ingredients:
                if any(qi in ing for ing in ing_list_lower) if isinstance(ing_list_lower, list) else qi in ing_list_lower:
                    matches += 1
            return matches
            
        results['match_score'] = results['ingredients'].apply(calculate_match_score)
        # Keep only entries with at least 1 match
        results = results[results['match_score'] > 0]
        results = results.sort_values(by='match_score', ascending=False)
        
    # Get top 5 results
    top_results = results.head(5)
    
    output = []
    for _, row in top_results.iterrows():
        output.append({
            "name": row.get("name"),
            "category": row.get("category"),
            "alcoholic": row.get("alcoholic"),
            "glassType": row.get("glassType"),
            "instructions": row.get("instructions"),
            "ingredients": row.get("ingredients"),
            "measures": row.get("ingredientMeasures"),
            "drinkThumbnail": row.get("drinkThumbnail"),
            "flavor_profile": row.get("flavor_profile"),
            "meaning_and_history": row.get("meaning_and_history"),
            "glassware_recommendation": row.get("glassware_recommendation"),
            "abv_category": row.get("abv_category")
        })
        
    return json.dumps({"cocktails": output}, ensure_ascii=False)


# -----------------------------------------------------------------------------
# Tool 2: db_search_bars
# -----------------------------------------------------------------------------
def db_search_bars(city: str = "", district: str = "", style: str = "", price_range: str = "") -> str:
    """
    Search for real cocktail bars in Vietnam based on city, district, vibe style, and price range.
    
    Args:
        city: City name ('Hanoi' or 'Ho Chi Minh City')
        district: District name (e.g., 'Hoan Kiem', 'District 1', 'District 3')
        style: Bar style/vibe (e.g., 'Speakeasy', 'Rooftop', 'Cozy Lounge', 'Jazz Bar', 'Craft Bar')
        price_range: Price level (options: '$', '$$', '$$$')
        
    Returns:
        JSON string containing a list of up to 5 matching bars
    """
    df = get_bars_df()
    if df.empty:
        return json.dumps({"error": "No bar data available."})
        
    results = df.copy()
    
    if city:
        results = results[results['city'].str.lower().str.contains(city.lower())]
    if district:
        results = results[results['district'].str.lower().str.contains(district.lower())]
    if style:
        results = results[results['style'].str.lower().str.contains(style.lower())]
    if price_range:
        results = results[results['price_range'] == price_range]
        
    top_results = results.head(5)
    
    output = []
    for _, row in top_results.iterrows():
        output.append({
            "name": row.get("name"),
            "city": row.get("city"),
            "district": row.get("district"),
            "address": row.get("address"),
            "style": row.get("style"),
            "price_range": row.get("price_range"),
            "signature_cocktail": row.get("signature_cocktail"),
            "vibe_description": row.get("vibe_description")
        })
        
    return json.dumps({"bars": output}, ensure_ascii=False)


# -----------------------------------------------------------------------------
# Tool 3: calculate_abv
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Tool 4: substitute_ingredient
# -----------------------------------------------------------------------------
def substitute_ingredient(missing_ingredient: str) -> str:
    """
    Suggest professional bartender substitutions for a missing cocktail ingredient.
    
    Args:
        missing_ingredient: The name of the missing ingredient (e.g., 'cointreau', 'bourbon')
        
    Returns:
        JSON string containing a list of substitutes and ratios
    """
    sub_map = {
        "cointreau": [
            {"substitute": "Triple Sec", "ratio": "1:1", "notes": "Similar orange flavor profile, suitable for Margaritas or Cosmopolitans."},
            {"substitute": "Grand Marnier", "ratio": "1:1", "notes": "Cognac-based orange liqueur, yields a richer flavor."}
        ],
        "triple sec": [
            {"substitute": "Cointreau", "ratio": "1:1", "notes": "Cointreau is less sweet and cleaner but acts as a perfect swap."},
            {"substitute": "Orange Curaçao", "ratio": "1:1", "notes": "Provides a slightly dry, classic orange profile."}
        ],
        "bourbon": [
            {"substitute": "Rye Whiskey", "ratio": "1:1", "notes": "Gives a spicier, drier taste profile compared to bourbon's sweet caramel notes."},
            {"substitute": "Irish Whiskey", "ratio": "1:1", "notes": "Gives a smoother, lighter finish."}
        ],
        "rye whiskey": [
            {"substitute": "Bourbon", "ratio": "1:1", "notes": "Bourbon is sweeter but works beautifully in an Old Fashioned or Manhattan."}
        ],
        "gin": [
            {"substitute": "Vodka", "ratio": "1:1", "notes": "Neutral spirit; will lack juniper botanical notes but works well if a cleaner taste is desired."}
        ],
        "vodka": [
            {"substitute": "White Rum", "ratio": "1:1", "notes": "White rum is slightly sweeter but replaces vodka well in fruit cocktails."}
        ],
        "lemon juice": [
            {"substitute": "Lime Juice", "ratio": "1:1", "notes": "Lime juice is slightly more acidic/sharp but is a very common swap."},
            {"substitute": "Diluted Citric Acid", "ratio": "1:1", "notes": "Used professionally to maintain consistent acidity."}
        ],
        "lime juice": [
            {"substitute": "Lemon Juice", "ratio": "1:1", "notes": "Lemon juice is milder and fresh."}
        ],
        "simple syrup": [
            {"substitute": "Honey Syrup", "ratio": "1:1", "notes": "Mix honey and warm water 1:1, brings a rich floral sweetness."},
            {"substitute": "Agave Nectar", "ratio": "0.75:1", "notes": "Agave is sweeter; reduce amount by 25%."}
        ],
        "angostura bitters": [
            {"substitute": "Peychaud's Bitters", "ratio": "1:1", "notes": "Anise and floral-forward profile, slightly sweeter."},
            {"substitute": "Orange Bitters", "ratio": "1:1", "notes": "Swaps herbal bitterness for a crisp citrus peel bitterness."}
        ],
        "campari": [
            {"substitute": "Aperol", "ratio": "1:1", "notes": "Aperol is lower ABV and sweeter, with about half the bitterness of Campari."}
        ],
        "vermouth": [
            {"substitute": "Lillet Blanc", "ratio": "1:1", "notes": "French aperitif wine, sweet and floral."}
        ]
    }
    
    ing_key = str(missing_ingredient).lower().strip()
    
    results = []
    for k, v in sub_map.items():
        if k in ing_key or ing_key in k:
            results.extend(v)
            break
            
    if not results:
        results = [{
            "substitute": "Vodka or similar neutral base spirit",
            "ratio": "1:1",
            "notes": "No specific replacement rules. Neutral spirit can be used to balance volume."
        }]
        
    return json.dumps({
        "missing_ingredient": missing_ingredient,
        "substitutes": results
    }, ensure_ascii=False)

# Tool schemas for Gemini Function Calling
TOOL_DECLARATIONS = [
    {
        "name": "db_search_cocktails",
        "description": "Searches for cocktails in the database by ingredients, category, flavor profile, and alcohol level.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ingredients_query": {
                    "type": "STRING",
                    "description": "Comma-separated ingredients list, e.g. 'gin, lemon, sugar'"
                },
                "category": {
                    "type": "STRING",
                    "description": "Cocktail category (e.g. 'Cocktail', 'Shot')"
                },
                "flavor": {
                    "type": "STRING",
                    "description": "Main flavor profile ('Chua', 'Ngọt', 'Đắng', 'Thảo mộc', 'Ấm nồng')"
                },
                "abv": {
                    "type": "STRING",
                    "description": "Alcohol category ('Mocktail (Không cồn)', 'Nhẹ (Low ABV)', 'Vừa (Medium ABV)', 'Mạnh (Strong ABV)')"
                }
            },
            "required": []
        }
    },
    {
        "name": "db_search_bars",
        "description": "Searches for actual premium cocktail bars in Vietnam (Hanoi & Ho Chi Minh City) by vibe style, price range, and district.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {
                    "type": "STRING",
                    "description": "City name ('Hanoi' or 'Ho Chi Minh City')"
                },
                "district": {
                    "type": "STRING",
                    "description": "District name in English without accents, e.g., 'Hoan Kiem', 'District 1', 'District 3'"
                },
                "style": {
                    "type": "STRING",
                    "description": "Bar vibe style ('Speakeasy', 'Rooftop', 'Cozy Lounge', 'Jazz Bar', 'Craft Bar')"
                },
                "price_range": {
                    "type": "STRING",
                    "description": "Price level ('$', '$$', '$$$')"
                }
            },
            "required": []
        }
    },
    {
        "name": "calculate_abv",
        "description": "Calculates estimated ABV percentage and classification of a cocktail based on ingredient volumes and their respective ABVs.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ingredients_with_ml": {
                    "type": "STRING",
                    "description": "JSON string containing ingredients and volume list, e.g., '[{\"name\": \"Gin\", \"abv\": 40, \"volume_ml\": 45}, {\"name\": \"Lime Juice\", \"abv\": 0, \"volume_ml\": 15}]'"
                }
            },
            "required": ["ingredients_with_ml"]
        }
    },
    {
        "name": "substitute_ingredient",
        "description": "Finds bartender substitutions for missing ingredients in a recipe.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "missing_ingredient": {
                    "type": "STRING",
                    "description": "The name of the missing ingredient, e.g., 'cointreau', 'bourbon', 'lemon juice'"
                }
            },
            "required": ["missing_ingredient"]
        }
    }
]

def execute_tool(name: str, args: dict) -> str:
    """Invokes the appropriate Python tool based on name"""
    if name == "db_search_cocktails":
        return db_search_cocktails(
            ingredients_query=args.get("ingredients_query", ""),
            category=args.get("category", ""),
            flavor=args.get("flavor", ""),
            abv=args.get("abv", "")
        )
    elif name == "db_search_bars":
        return db_search_bars(
            city=args.get("city", ""),
            district=args.get("district", ""),
            style=args.get("style", ""),
            price_range=args.get("price_range", "")
        )
    elif name == "calculate_abv":
        return calculate_abv(ingredients_with_ml=args.get("ingredients_with_ml", "[]"))
    elif name == "substitute_ingredient":
        return substitute_ingredient(missing_ingredient=args.get("missing_ingredient", ""))
    else:
        return json.dumps({"error": f"Tool '{name}' not found."})
