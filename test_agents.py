import sys
from pathlib import Path

# Add project root to python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.agents.cocktail_agents import CocktailAgentSystem

def test_system():
    print("Initializing CocktailAgentSystem...")
    try:
        system = CocktailAgentSystem()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return

    # 1. Test Guest Agent seeking bar
    print("\n--- Testing Guest Agent (Bar recommendation) ---")
    query_bar = "Can you recommend a speakeasy bar in Hoan Kiem district?"
    print(f"User: {query_bar}")
    res_bar = system.run_chat(query_bar, [], "guest")
    print(f"AI: {res_bar['message']}")
    
    # 2. Test Bartender Agent seeking substitution
    print("\n--- Testing Bartender Agent (Ingredient substitution) ---")
    query_sub = "I don't have Cointreau for my Margarita, what is a professional substitute?"
    print(f"User: {query_sub}")
    res_sub = system.run_chat(query_sub, [], "bartender")
    print(f"AI: {res_sub['message']}")

if __name__ == "__main__":
    test_system()
