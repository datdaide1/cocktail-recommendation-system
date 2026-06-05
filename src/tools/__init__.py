import json
from src.tools.db_search import db_search_cocktails, db_search_bars
from src.tools.calculators import calculate_abv, calculate_cost_and_shopping_list
from src.tools.mixology import substitute_ingredient, generate_custom_recipe, recommend_food_pairing

# Aggregate schemas for all tool capabilities
TOOL_DECLARATIONS = [
    {
        "name": "db_search_cocktails",
        "description": "Searches for cocktails in the database using hybrid search combining exact filters and free-text semantic vibe/mood queries.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Free-text vibe, mood, feeling, context, or style description (e.g., 'sweet romantic summer sunset drink', 'strong warm winter night cap')"
                },
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
    },
    {
        "name": "calculate_cost_and_shopping_list",
        "description": "Estimates the retail cost of ingredients in VND for making cocktails and generates a structured shopping list.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ingredients_list": {
                    "type": "STRING",
                    "description": "Comma-separated list of ingredients needed, e.g., 'gin, tonic, lime'"
                }
            },
            "required": ["ingredients_list"]
        }
    },
    {
        "name": "generate_custom_recipe",
        "description": "Searches for matching reference baseline cocktail recipes in the database to help guide creating a custom drink.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "available_ingredients": {
                    "type": "STRING",
                    "description": "Comma-separated list of ingredients you have, e.g., 'gin, strawberry, honey'"
                },
                "vibe": {
                    "type": "STRING",
                    "description": "Target style or mood of the cocktail, e.g., 'refreshing', 'strong', 'sweet'"
                }
            },
            "required": ["available_ingredients"]
        }
    },
    {
        "name": "recommend_food_pairing",
        "description": "Suggests food pairings and snacks for a cocktail based on its flavor profile.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "flavor_profile": {
                    "type": "STRING",
                    "description": "Flavor description, e.g., 'Sweet', 'Sour', 'Bitter', 'Herbaceous', 'Spicy'"
                },
                "cocktail_name": {
                    "type": "STRING",
                    "description": "Name of the cocktail"
                }
            },
            "required": []
        }
    }
]

def execute_tool(name: str, args: dict) -> str:
    """Invokes the appropriate Python tool based on name"""
    if name == "db_search_cocktails":
        return db_search_cocktails(
            query=args.get("query", ""),
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
    elif name == "calculate_cost_and_shopping_list":
        return calculate_cost_and_shopping_list(ingredients_list=args.get("ingredients_list", ""))
    elif name == "generate_custom_recipe":
        return generate_custom_recipe(
            available_ingredients=args.get("available_ingredients", ""),
            vibe=args.get("vibe", "")
        )
    elif name == "recommend_food_pairing":
        return recommend_food_pairing(
            flavor_profile=args.get("flavor_profile", ""),
            cocktail_name=args.get("cocktail_name", "")
        )
    else:
        return json.dumps({"error": f"Tool '{name}' not found."})
