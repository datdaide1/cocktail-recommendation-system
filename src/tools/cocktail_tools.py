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
    Tìm kiếm cocktail trong cơ sở dữ liệu dựa trên nguyên liệu, phân loại, hương vị hoặc độ mạnh của cồn.
    
    Args:
        ingredients_query: Chuỗi chứa các nguyên liệu ngăn cách bằng dấu phẩy (ví dụ: 'gin, chanh')
        category: Thể loại cocktail (ví dụ: 'Cocktail', 'Shot', 'Ordinary Drink')
        flavor: Hương vị mong muốn (chọn từ: 'Chua', 'Ngọt', 'Đắng', 'Thảo mộc', 'Ấm nồng')
        abv: Phân loại cồn (chọn từ: 'Mocktail (Không cồn)', 'Nhẹ (Low ABV)', 'Vừa (Medium ABV)', 'Mạnh (Strong ABV)')
        
    Returns:
        JSON string danh sách tối đa 5 cocktail phù hợp nhất
    """
    df = get_cocktails_df()
    if df.empty:
        return json.dumps({"error": "Không có dữ liệu cocktail."})
        
    results = df.copy()
    
    # 1. Lọc theo Phân loại (Category)
    if category:
        results = results[results['category'].str.lower().str.contains(category.lower())]
        
    # 2. Lọc theo Hương vị (Flavor)
    if flavor:
        results = results[results['flavor_profile'].str.lower().str.contains(flavor.lower())]
        
    # 3. Lọc theo Phân loại Cồn (ABV)
    if abv:
        results = results[results['abv_category'].str.lower().str.contains(abv.lower())]
        
    # 4. Tìm kiếm theo Nguyên liệu (Ingredients)
    if ingredients_query:
        query_ingredients = [i.strip().lower() for i in ingredients_query.split(',') if i.strip()]
        
        def calculate_match_score(ingredients_list_str):
            # Parse list of ingredients from string
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
        # Chỉ giữ lại các cocktail có ít nhất 1 nguyên liệu khớp
        results = results[results['match_score'] > 0]
        results = results.sort_values(by='match_score', ascending=False)
        
    # Lấy top 5 kết quả
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
        
    return json.dumps(output, ensure_ascii=False)


# -----------------------------------------------------------------------------
# Tool 2: db_search_bars
# -----------------------------------------------------------------------------
def db_search_bars(city: str = "", district: str = "", style: str = "", price_range: str = "") -> str:
    """
    Tìm kiếm các quán bar thực tế tại Việt Nam dựa trên thành phố, quận, phong cách và tầm giá.
    
    Args:
        city: Tên thành phố ('Hanoi' hoặc 'Ho Chi Minh City')
        district: Tên quận (ví dụ: 'Hoan Kiem', 'District 1', 'District 3')
        style: Phong cách quán ('Speakeasy', 'Rooftop', 'Cozy Lounge', 'Jazz Bar', 'Craft Bar', 'Luxury Bar')
        price_range: Tầm giá (chọn từ: '$', '$$', '$$$')
        
    Returns:
        JSON string danh sách tối đa 5 quán bar phù hợp
    """
    df = get_bars_df()
    if df.empty:
        return json.dumps({"error": "Không có dữ liệu quán bar."})
        
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
        
    return json.dumps(output, ensure_ascii=False)


# -----------------------------------------------------------------------------
# Tool 3: calculate_abv
# -----------------------------------------------------------------------------
def calculate_abv(ingredients_with_ml: str) -> str:
    """
    Tính toán nồng độ cồn ước tính (ABV - Alcohol By Volume) của một ly cocktail dựa trên danh sách các nguyên liệu cồn và thể tích của chúng.
    
    Args:
        ingredients_with_ml: Chuỗi JSON đại diện cho danh sách các nguyên liệu, ví dụ:
          '[{"name": "Gin", "abv": 40, "volume_ml": 45}, {"name": "Lime Juice", "abv": 0, "volume_ml": 15}]'
          
    Returns:
        JSON string chứa kết quả tính ABV phần trăm và phân hạng mức độ mạnh
    """
    try:
        items = json.loads(ingredients_with_ml)
    except Exception as e:
        return json.dumps({"error": f"Lỗi định dạng JSON đầu vào: {e}"})
        
    total_volume = 0.0
    total_alcohol = 0.0
    
    for item in items:
        vol = float(item.get("volume_ml", 0.0))
        abv = float(item.get("abv", 0.0))
        
        total_volume += vol
        total_alcohol += (vol * abv / 100.0)
        
    if total_volume == 0:
        return json.dumps({"error": "Tổng thể tích đồ uống phải lớn hơn 0ml."})
        
    final_abv = (total_alcohol / total_volume) * 100.0
    
    if final_abv == 0:
        abv_category = "Mocktail (Không cồn)"
    elif final_abv < 10:
        abv_category = "Nhẹ (Low ABV)"
    elif final_abv < 20:
        abv_category = "Vừa (Medium ABV)"
    else:
        abv_category = "Mạnh (Strong ABV)"
        
    result = {
        "total_volume_ml": round(total_volume, 1),
        "estimated_abv": round(final_abv, 1),
        "abv_category": abv_category,
        "description": f"Ly cocktail có tổng thể tích là {round(total_volume, 1)}ml với nồng độ cồn ước tính khoảng {round(final_abv, 1)}% ({abv_category})."
    }
    
    return json.dumps(result, ensure_ascii=False)


# -----------------------------------------------------------------------------
# Tool 4: substitute_ingredient
# -----------------------------------------------------------------------------
def substitute_ingredient(missing_ingredient: str) -> str:
    """
    Đưa ra các giải pháp thay thế chuẩn chuyên nghiệp cho một nguyên liệu cocktail bị thiếu.
    
    Args:
        missing_ingredient: Tên nguyên liệu bị thiếu (ví dụ: 'cointreau', 'bourbon')
        
    Returns:
        JSON string chứa danh sách các nguyên liệu thay thế và tỷ lệ tương ứng
    """
    sub_map = {
        "cointreau": [
            {"substitute": "Triple Sec", "ratio": "1:1", "notes": "Hương cam ngọt ngào tương đương, phù hợp cho Margarita hoặc Cosmopolitan."},
            {"substitute": "Grand Marnier", "ratio": "1:1", "notes": "Hương cam đậm đặc hơn trên nền rượu cognac, mang lại vị đậm đà hơn."}
        ],
        "triple sec": [
            {"substitute": "Cointreau", "ratio": "1:1", "notes": "Cointreau tinh tế và ít ngọt hơn một chút nhưng thay thế hoàn hảo."},
            {"substitute": "Orange Curaçao", "ratio": "1:1", "notes": "Mang hương cam hơi chát nhẹ cổ điển hơn."}
        ],
        "bourbon": [
            {"substitute": "Rye Whiskey", "ratio": "1:1", "notes": "Cho vị cay nồng và khô hơn so với vị ngọt caramel đặc trưng của Bourbon."},
            {"substitute": "Irish Whiskey", "ratio": "1:1", "notes": "Cho vị nhẹ nhàng, mượt mà hơn."}
        ],
        "rye whiskey": [
            {"substitute": "Bourbon", "ratio": "1:1", "notes": "Bourbon sẽ ngọt hơn một chút nhưng thay thế rất tốt trong Old Fashioned hay Manhattan."}
        ],
        "gin": [
            {"substitute": "Vodka", "ratio": "1:1", "notes": "Vodka là rượu trung tính, sẽ thiếu đi mùi thảo mộc quả thông của Gin nhưng thay thế tốt nếu cần uống nhẹ vị."}
        ],
        "vodka": [
            {"substitute": "White Rum", "ratio": "1:1", "notes": "Rum trắng sẽ ngọt nhẹ hơn nhưng thay thế tốt trong các loại cocktail trái cây."}
        ],
        "lemon juice": [
            {"substitute": "Lime Juice", "ratio": "1:1", "notes": "Nước cốt chanh xanh có vị chua sắc hơn chanh vàng nhưng thay thế cực kỳ phổ biến."},
            {"substitute": "Axit Citric pha loãng", "ratio": "1:1", "notes": "Thích hợp khi pha chế chuyên nghiệp để kiểm soát độ chua ổn định."}
        ],
        "lime juice": [
            {"substitute": "Lemon Juice", "ratio": "1:1", "notes": "Nước cốt chanh vàng thơm mát và có vị chua dịu hơn."}
        ],
        "simple syrup": [
            {"substitute": "Honey Syrup", "ratio": "1:1", "notes": "Pha mật ong với nước ấm theo tỉ lệ 1:1, đem lại vị ngọt thanh tự nhiên thơm ngon."},
            {"substitute": "Agave Nectar", "ratio": "0.75:1", "notes": "Mật cây thùa rất ngọt, hãy giảm bớt 25% lượng dùng so với syrup thông thường."}
        ],
        "angostura bitters": [
            {"substitute": "Peychaud's Bitters", "ratio": "1:1", "notes": "Mang hương vị cam thảo và hoa cỏ ngọt hơn nhẹ nhàng hơn."},
            {"substitute": "Orange Bitters", "ratio": "1:1", "notes": "Thay đổi vị đắng thảo mộc sang vị đắng vỏ cam tươi mát."}
        ],
        "campari": [
            {"substitute": "Aperol", "ratio": "1:1", "notes": "Aperol có nồng độ cồn thấp hơn và ngọt hơn Campari (độ đắng giảm đi một nửa)."}
        ],
        "vermouth": [
            {"substitute": "Lillet Blanc", "ratio": "1:1", "notes": "Rượu vang khai vị Pháp ngọt dịu và thơm hương hoa cỏ."}
        ]
    }
    
    ing_key = str(missing_ingredient).lower().strip()
    
    # Tìm kiếm gần đúng trong từ điển
    results = []
    for k, v in sub_map.items():
        if k in ing_key or ing_key in k:
            results.extend(v)
            break
            
    if not results:
        # Fallback thông báo chung
        results = [{
            "substitute": "Vodka hoặc Rượu nền trung tính tương đương",
            "ratio": "1:1",
            "notes": "Chúng tôi chưa có dữ liệu thay thế cụ thể cho nguyên liệu này. Bạn có thể thay thế bằng rượu nền nhẹ vị hoặc liên hệ Master Bartender để được gợi ý nâng cao."
        }]
        
    return json.dumps({
        "missing_ingredient": missing_ingredient,
        "substitutes": results
    }, ensure_ascii=False)

# Bọc các tool để khai báo cho Gemini API
TOOL_DECLARATIONS = [
    {
        "name": "db_search_cocktails",
        "description": "Tìm kiếm các ly cocktail trong cơ sở dữ liệu theo nguyên liệu, thể loại, hương vị và phân hạng cồn.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ingredients_query": {
                    "type": "STRING",
                    "description": "Các nguyên liệu cách nhau bằng dấu phẩy, ví dụ: 'gin, chanh, đường'"
                },
                "category": {
                    "type": "STRING",
                    "description": "Thể loại cocktail (ví dụ: 'Cocktail', 'Shot')"
                },
                "flavor": {
                    "type": "STRING",
                    "description": "Hương vị chính mong muốn ('Chua', 'Ngọt', 'Đắng', 'Thảo mộc', 'Ấm nồng')"
                },
                "abv": {
                    "type": "STRING",
                    "description": "Mức độ cồn ('Mocktail (Không cồn)', 'Nhẹ (Low ABV)', 'Vừa (Medium ABV)', 'Mạnh (Strong ABV)')"
                }
            },
            "required": []
        }
    },
    {
        "name": "db_search_bars",
        "description": "Tìm kiếm các quán bar thực tế nổi tiếng ở Hà Nội và Hồ Chí Minh theo phong cách, tầm giá, quận.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {
                    "type": "STRING",
                    "description": "Tên thành phố ('Hanoi' hoặc 'Ho Chi Minh City')"
                },
                "district": {
                    "type": "STRING",
                    "description": "Tên quận bằng tiếng Anh không dấu, ví dụ: 'Hoan Kiem', 'District 1', 'District 3'"
                },
                "style": {
                    "type": "STRING",
                    "description": "Phong cách quán ('Speakeasy', 'Rooftop', 'Cozy Lounge', 'Jazz Bar', 'Craft Bar')"
                },
                "price_range": {
                    "type": "STRING",
                    "description": "Tầm giá của quán ('$', '$$', '$$$')"
                }
            },
            "required": []
        }
    },
    {
        "name": "calculate_abv",
        "description": "Tính toán nồng độ cồn ABV và phân loại độ mạnh của ly cocktail dựa trên lượng ml và ABV của nguyên liệu thành phần.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ingredients_with_ml": {
                    "type": "STRING",
                    "description": "Chuỗi JSON chứa danh sách nguyên liệu và thể tích ml, ví dụ: '[{\"name\": \"Gin\", \"abv\": 40, \"volume_ml\": 45}, {\"name\": \"Chanh\", \"abv\": 0, \"volume_ml\": 15}]'"
                }
            },
            "required": ["ingredients_with_ml"]
        }
    },
    {
        "name": "substitute_ingredient",
        "description": "Tìm kiếm nguyên liệu thay thế chuẩn pha chế khi bị thiếu một nguyên liệu nào đó trong công thức.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "missing_ingredient": {
                    "type": "STRING",
                    "description": "Tên nguyên liệu bị thiếu, ví dụ: 'cointreau', 'bourbon', 'lemon juice'"
                }
            },
            "required": ["missing_ingredient"]
        }
    }
]

def execute_tool(name: str, args: dict) -> str:
    """Hàm trung gian để thực thi các tool bằng tên"""
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
        return json.dumps({"error": f"Tool '{name}' không tồn tại."})
