import pytest
import logging
from app.tools.cost_abv_calculator import calculate_cost_and_abv
from app.tools.substitution_engine import get_ingredient_substitutes

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_calculate_cost_and_abv_known_ingredients():
    """
    Test calculate_cost_and_abv with a known set of ingredients (Absolut Vodka and water/juice).
    Assert that cost and ABV math is calculated perfectly.
    """
    ingredients = [
        {"name": "Absolut Vodka", "volume_ml": 50},
        {"name": "Water", "volume_ml": 150}
    ]
    
    result = await calculate_cost_and_abv(ingredients)
    
    # Assertions for totals
    assert result["total_volume_ml"] == 200.0
    # Absolut Vodka: 350000 VND / 700ml = 500 VND/ml. 50ml * 500 VND/ml = 25000 VND
    # Water: 0 VND
    assert result["total_cost_vnd"] == 25000.0
    # Absolut Vodka ABV = 40%. Pure alcohol = 50 * 0.40 = 20ml
    # Water ABV = 0%. Pure alcohol = 0ml
    # Total pure alcohol = 20ml. Total volume = 200ml. ABV = (20 / 200) * 100 = 10%
    assert result["abv"] == 10.0
    
    # Breakdown assertions
    assert len(result["breakdown"]) == 2
    
    vodka_item = next(item for item in result["breakdown"] if "Vodka" in item["name"])
    assert vodka_item["volume_ml"] == 50.0
    assert vodka_item["cost"] == 25000.0
    assert vodka_item["abv"] == 40.0
    
    water_item = next(item for item in result["breakdown"] if "Water" in item["name"])
    assert water_item["volume_ml"] == 150.0
    assert water_item["cost"] == 0.0
    assert water_item["abv"] == 0.0


@pytest.mark.asyncio
async def test_calculate_cost_and_abv_case_insensitivity_and_spacing():
    """
    Test case insensitivity and whitespace stripping for ingredient lookup.
    """
    ingredients = [
        {"name": "  absolut vodka  ", "volume_ml": 100}
    ]
    
    result = await calculate_cost_and_abv(ingredients)
    
    assert result["total_volume_ml"] == 100.0
    assert result["total_cost_vnd"] == 50000.0  # 100 * 500
    assert result["abv"] == 40.0


@pytest.mark.asyncio
async def test_calculate_cost_and_abv_unknown_ingredients():
    """
    Test calculate_cost_and_abv with unknown ingredients to verify fallback behavior (ABV 0, Price 0).
    """
    ingredients = [
        {"name": "Mysterious Liquid X", "volume_ml": 100}
    ]
    
    result = await calculate_cost_and_abv(ingredients)
    
    assert result["total_volume_ml"] == 100.0
    assert result["total_cost_vnd"] == 0.0
    assert result["abv"] == 0.0
    
    assert len(result["breakdown"]) == 1
    assert result["breakdown"][0]["name"] == "Mysterious Liquid X"
    assert result["breakdown"][0]["cost"] == 0.0
    assert result["breakdown"][0]["abv"] == 0.0


@pytest.mark.asyncio
async def test_get_ingredient_substitutes_known():
    """
    Test get_ingredient_substitutes with a known ingredient (e.g., Cointreau)
    to assert that the list of substitutes and notes match.
    """
    result = await get_ingredient_substitutes("Cointreau")
    
    assert isinstance(result["substitutes"], list)
    assert len(result["substitutes"]) > 0
    assert "Triple Sec" in result["substitutes"]
    assert "notes" in result
    assert "Triple Sec is a direct cheaper swap" in result["notes"]


@pytest.mark.asyncio
async def test_get_ingredient_substitutes_case_insensitive():
    """
    Test get_ingredient_substitutes is case-insensitive and strips spacing.
    """
    result = await get_ingredient_substitutes("  cointreau  ")
    
    assert len(result["substitutes"]) > 0
    assert "Triple Sec" in result["substitutes"]


@pytest.mark.asyncio
async def test_get_ingredient_substitutes_unknown():
    """
    Test get_ingredient_substitutes with an unknown ingredient to verify empty list and message.
    """
    result = await get_ingredient_substitutes("Super Rare Exotic Fruit")
    
    assert result["substitutes"] == []
    assert "No substitutes found" in result["notes"]
    assert "message" in result
    assert "No substitutes found" in result["message"]
