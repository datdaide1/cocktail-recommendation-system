import sys
import json
from pathlib import Path

# Add project root to python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.agents.cocktail_agents import CocktailAgentSystem
from src.tools import execute_tool

def run_test_scenario(system, name, query, role):
    print(f"\n==================================================")
    print(f"Scenario: {name}")
    print(f"User ({role}): {query}")
    print(f"==================================================")
    try:
        res = system.run_chat(query, [], role)
        print(f"AI Response:\n{res['message']}\n")
        # Print actual history size
        print(f"History elements returned: {len(res['chat_history'])}")
        return res
    except Exception as e:
        print(f"Test failed with error: {e}")
        return None

def test_advanced_scenarios():
    print("Initializing CocktailAgentSystem for Advanced Testing...")
    try:
        system = CocktailAgentSystem()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return

    # --- Scenario 1: The Picky Customer ---
    # Customer has allergic exclusions (no lime, no gin), wants sweet, and low ABV.
    run_test_scenario(
        system,
        "1. The Picky Customer (Lime Allergy, No Gin, Sweet, Low ABV)",
        "I want a cocktail recommendation, but I have a severe lime allergy and I absolutely hate gin. It must be sweet and low alcohol (Low ABV).",
        "guest"
    )

    # --- Scenario 2: The Clueless Customer (Vague Mood & Colors) ---
    # Customer knows nothing about cocktails, only colors and moods.
    run_test_scenario(
        system,
        "2. The Clueless Customer (Mood & Color-based request)",
        "Hi, I had a terrible day and I feel very blue. Can you suggest a sweet red drink to make me happy?",
        "guest"
    )

    # --- Scenario 3: Clueless Customer (One-word vague query) ---
    run_test_scenario(
        system,
        "3. The Vague Customer (Single word)",
        "something red",
        "guest"
    )

    # --- Scenario 4: Master Bartender Edge Case (ABV calculation with gibberish) ---
    # Customer tries to calculate ABV but inputs invalid format
    run_test_scenario(
        system,
        "4. Mixology Edge Case (Malformed ABV inputs)",
        "Can you calculate the ABV for a drink? Here's the recipe: 50ml gin and 100ml water. But do it with a broken list.",
        "bartender"
    )

    # --- Scenario 5: Master Bartender Edge Case (Unicorn Tears Substitution) ---
    # Customer asks for substitution of a non-existent mythical ingredient
    run_test_scenario(
        system,
        "5. Mixology Edge Case (Mythical ingredient substitution)",
        "I am trying to make a magical potion and I'm missing 'unicorn tears'. What can I substitute it with?",
        "bartender"
    )

    # --- Scenario 6: Shopping List Costing ---
    run_test_scenario(
        system,
        "6. Party planner (Shopping List & Cost estimation)",
        "I want to make a party with 3 drinks: Mojito, Negroni, and Margarita. Can you list the ingredients I need to buy (gin, rum, tequila, campari, vermouth, lime, mint, sugar, tonic) and estimate how much it will cost in VND?",
        "bartender"
    )

if __name__ == "__main__":
    test_advanced_scenarios()
