import json
from src.tools.base import get_cocktails_df

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

def generate_custom_recipe(available_ingredients: str, vibe: str = "") -> str:
    """
    Finds real base reference recipes in our database that contain some of the user's available ingredients.
    This provides reference structures and ratios for the mixology agent to design a new custom recipe.
    
    Args:
        available_ingredients: Comma-separated list of ingredients the user has, e.g., 'vodka, cranberry, orange'
        vibe: The target mood or style for the custom recipe (e.g. 'refreshing', 'cozy', 'herbal')
        
    Returns:
        JSON string containing matching baseline reference cocktail recipes.
    """
    df = get_cocktails_df()
    if df.empty:
        return json.dumps({"error": "No database recipe references available."})
        
    items = [i.strip().lower() for i in available_ingredients.split(',') if i.strip()]
    if not items:
        return json.dumps({"error": "Please specify at least one available ingredient."})
        
    # Find cocktails in database containing any of these ingredients
    matches = []
    for _, row in df.iterrows():
        ingredients_list_str = row.get("ingredients", "")
        try:
            ing_list = eval(ingredients_list_str)
            ing_list_lower = [str(i).lower() for i in ing_list]
        except:
            ing_list_lower = str(ingredients_list_str).lower()
            
        score = 0
        for item in items:
            if any(item in ing for ing in ing_list_lower) if isinstance(ing_list_lower, list) else item in ing_list_lower:
                score += 1
                
        if score > 0:
            matches.append((score, row))
            
    # Sort by score descending and take top 3
    matches.sort(key=lambda x: x[0], reverse=True)
    top_matches = matches[:3]
    
    output = []
    for score, row in top_matches:
        output.append({
            "name": row.get("name"),
            "ingredients": row.get("ingredients"),
            "measures": row.get("ingredientMeasures"),
            "instructions": row.get("instructions"),
            "matching_ingredients_count": score
        })
        
    return json.dumps({
        "available_ingredients": items,
        "vibe": vibe,
        "reference_baselines": output
    }, ensure_ascii=False)

def recommend_food_pairing(flavor_profile: str = "", cocktail_name: str = "") -> str:
    """
    Suggests premium food and snack pairings for a cocktail based on its flavor profile or name.
    
    Args:
        flavor_profile: The main flavor profile (e.g. 'Sweet', 'Sour', 'Bitter', 'Herbaceous', 'Spicy')
        cocktail_name: Optional name of a specific cocktail (e.g. 'Negroni', 'Mojito')
        
    Returns:
        JSON string containing suggested food pairings and culinary explanations.
    """
    pairings_catalog = {
        "sweet": [
            {"food": "Artisanal Cheese Board (Blue cheese, Aged Gouda)", "explanation": "The salty, savory profile of aged cheeses balances the intense sweetness of the drink."},
            {"food": "Spicy Meatballs or Chorizo", "explanation": "Spicy, savory bites create a satisfying contrast with sweet notes."}
        ],
        "sour": [
            {"food": "Fried Calamari or Seafood Tempura", "explanation": "The bright acidity of a sour drink cuts beautifully through rich, fried seafood."},
            {"food": "Salted Cashews and Edamame", "explanation": "Salt enhances the citrus character of sour drinks."}
        ],
        "bitter": [
            {"food": "70% Dark Chocolate or Chocolate Truffles", "explanation": "The cocoa bitterness complements drinks like Negronis or Boulevadiers without adding cloying sweetness."},
            {"food": "Prosciutto and Cured Meats", "explanation": "Rich fats and salt cut the sharp herbal bitterness of digestifs."}
        ],
        "herbaceous": [
            {"food": "Garlic Bruschetta with Tomato and Basil", "explanation": "Complements the fresh, botanical notes of gin and herbal liqueurs."},
            {"food": "Marinated Green Olives", "explanation": "Salty, green elements pair beautifully with botanical notes."}
        ],
        "spicy": [
            {"food": "Sweet Chili Spring Rolls", "explanation": "Sweet chili glaze softens the alcohol burn and highlights warm spice profiles."},
            {"food": "Roasted Glazed Almonds", "explanation": "Warm, nutty flavors enrich cinnamon or ginger notes."}
        ]
    }
    
    selected_flavor = str(flavor_profile).lower().strip()
    
    # Simple lookup based on keywords
    pairings = []
    if "ngọt" in selected_flavor or "sweet" in selected_flavor:
        pairings = pairings_catalog["sweet"]
    elif "chua" in selected_flavor or "sour" in selected_flavor:
        pairings = pairings_catalog["sour"]
    elif "đắng" in selected_flavor or "bitter" in selected_flavor:
        pairings = pairings_catalog["bitter"]
    elif "thảo mộc" in selected_flavor or "herb" in selected_flavor:
        pairings = pairings_catalog["herbaceous"]
    elif "ấm nồng" in selected_flavor or "spic" in selected_flavor:
        pairings = pairings_catalog["spicy"]
    else:
        # Fallback to sour/sweet default
        pairings = pairings_catalog["sour"]
        
    return json.dumps({
        "cocktail_name": cocktail_name,
        "flavor_profile": flavor_profile,
        "suggested_pairings": pairings
    }, ensure_ascii=False)
