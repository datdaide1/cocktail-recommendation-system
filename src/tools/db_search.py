import json
from src.tools.base import get_cocktails_df, get_bars_df

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
        results = results[results['category'].str.lower().str.contains(category.lower(), regex=False)]
        
    # 2. Filter by Flavor
    if flavor:
        results = results[results['flavor_profile'].str.lower().str.contains(flavor.lower(), regex=False)]
        
    # 3. Filter by ABV Category
    if abv:
        results = results[results['abv_category'].str.lower().str.contains(abv.lower(), regex=False)]
        
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
        results = results[results['city'].str.lower().str.contains(city.lower(), regex=False)]
    if district:
        results = results[results['district'].str.lower().str.contains(district.lower(), regex=False)]
    if style:
        results = results[results['style'].str.lower().str.contains(style.lower(), regex=False)]
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
