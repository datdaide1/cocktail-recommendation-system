import os
import pandas as pd
import numpy as np
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def get_gemini_client():
    provider = os.getenv("LLM_PROVIDER", "").lower()
    
    # 9router / Custom Provider
    custom_key = os.getenv("CUSTOM_API_KEY")
    custom_base = os.getenv("CUSTOM_API_BASE")
    if (provider == "custom" or custom_key) and custom_base:
        print(f"Using 9router (Custom) Provider for enrichment at {custom_base}")
        return {"type": "custom", "api_key": custom_key, "api_base": custom_base, "model": os.getenv("CUSTOM_MODEL", "beeknoee/gemini-3.5-flash")}
        
    # OpenRouter Provider
    or_key = os.getenv("OPENROUTER_API_KEY")
    if provider == "openrouter" or or_key:
        print(f"Using OpenRouter Provider for enrichment")
        return {"type": "openrouter", "api_key": or_key, "model": os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-lite-preview-02-05:free")}
        
    # Native Gemini Provider
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("Warning: No valid API key found. Using local fallback rule-based enrichment.")
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.1-flash-lite")
        print("Using Native Gemini SDK for enrichment")
        return {"type": "gemini", "model": model}
    except Exception as e:
        print(f"Error configuring Gemini API: {e}. Falling back to rule-based enrichment.")
        return None


def fetch_cocktail_image(name):
    import requests
    import urllib.parse
    try:
        url = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={urllib.parse.quote(name)}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data and data.get("drinks") and len(data["drinks"]) > 0:
                return data["drinks"][0].get("strDrinkThumb", "")
    except Exception as e:
        print(f"Warning: Failed to fetch image for {name} - {e}")
    return ""

def fallback_enrich(row):
    """Fallback function to enrich metadata using simple heuristics if Gemini is not available"""
    ingredients_lower = str(row.get('ingredients', '')).lower()
    category_lower = str(row.get('category', '')).lower()
    alcoholic = str(row.get('alcoholic', '')).lower()
    
    # Flavor profile
    flavors = []
    if any(x in ingredients_lower for x in ['lemon', 'lime', 'citrus', 'orange', 'sour']):
        flavors.append("Chua (Sour)")
    if any(x in ingredients_lower for x in ['sugar', 'syrup', 'grenadine', 'honey', 'liqueur', 'sweet']):
        flavors.append("Ngọt (Sweet)")
    if any(x in ingredients_lower for x in ['campari', 'tonic', 'bitters', 'coffee', 'espresso', 'aperol']):
        flavors.append("Đắng (Bitter)")
    if any(x in ingredients_lower for x in ['mint', 'basil', 'rosemary', 'herb', 'ginger', 'pepper']):
        flavors.append("Thảo mộc (Herbal)")
    if any(x in ingredients_lower for x in ['whiskey', 'scotch', 'bourbon', 'mezcal', 'rum']):
        flavors.append("Ấm nồng (Warm/Spicy)")
    if not flavors:
        flavors = ["Cân bằng (Balanced)"]
    flavor_profile = ", ".join(flavors)
    
    # History & Meaning
    name = row.get('name', 'Cocktail')
    meaning_and_history = f"Ly {name} là sự kết hợp tinh tế giữa các thành phần cổ điển. " \
                          f"Nó mang đậm phong cách thưởng thức cocktail truyền thống và được yêu thích bởi hương vị hài hòa."
    
    # Glassware
    glass = row.get('glassType', 'Cocktail glass')
    if 'martini' in str(glass).lower():
        glassware_recommendation = "Ly Martini"
    elif 'highball' in str(glass).lower():
        glassware_recommendation = "Ly Highball"
    elif 'shot' in str(glass).lower():
        glassware_recommendation = "Ly Shot"
    elif 'champagne' in str(glass).lower():
        glassware_recommendation = "Ly Flute (Champagne)"
    else:
        glassware_recommendation = "Ly Cocktail tiêu chuẩn"
        
    # ABV Category
    if 'non' in alcoholic or 'zero' in alcoholic:
        abv_category = "Mocktail (Không cồn)"
    elif any(x in ingredients_lower for x in ['beer', 'wine', 'vermouth', 'cider', 'sherry']):
        abv_category = "Nhẹ (Low ABV)"
    elif any(x in ingredients_lower for x in ['vodka', 'gin', 'rum', 'whiskey', 'tequila', 'brandy']):
        if len(ingredients_lower.split(',')) <= 3:
            abv_category = "Mạnh (Strong ABV)"
        else:
            abv_category = "Vừa (Medium ABV)"
    else:
        abv_category = "Vừa (Medium ABV)"
        
    return pd.Series([flavor_profile, meaning_and_history, glassware_recommendation, abv_category])

def main():
    base_dir = Path(__file__).resolve().parent.parent
    raw_csv_path = base_dir / "data" / "raw" / "final_cocktails.csv"
    output_csv_path = base_dir / "data" / "enriched_cocktails.csv"
    
    if not raw_csv_path.exists():
        print(f"Error: Raw CSV not found at {raw_csv_path}")
        return
        
    print(f"Loading dataset from {raw_csv_path}...")
    df = pd.read_csv(raw_csv_path)
    print(f"Found {len(df)} cocktails.")
    
    model = get_gemini_client()
    
    # Initialize new columns
    df['flavor_profile'] = ""
    df['meaning_and_history'] = ""
    df['glassware_recommendation'] = ""
    df['abv_category'] = ""
    df['image_url'] = ""
    
    if model is None:
        print("Running fast local rule-based enrichment...")
        enriched = df.apply(fallback_enrich, axis=1)
        df[['flavor_profile', 'meaning_and_history', 'glassware_recommendation', 'abv_category']] = enriched
    else:
        print("Starting AI-powered enrichment using Gemini. Processing first 30 rows using LLM and the rest using rule-based fallback for efficiency...")
        for idx, row in df.iterrows():
            name = row.get('name')
            
            # Use Gemini for first 30, and rule-based for the rest to avoid long wait
            if idx >= 30:
                fallback_res = fallback_enrich(row)
                df.at[idx, 'flavor_profile'] = fallback_res[0]
                img = fetch_cocktail_image(name)
                df.at[idx, 'image_url'] = img
                img = fetch_cocktail_image(name)
                df.at[idx, 'image_url'] = img
                df.at[idx, 'meaning_and_history'] = fallback_res[1]
                df.at[idx, 'glassware_recommendation'] = fallback_res[2]
                df.at[idx, 'abv_category'] = fallback_res[3]
                continue
                
            ingredients = row.get('ingredients')
            instructions = row.get('instructions')
            
            prompt = f"""
            Bạn là chuyên gia pha chế cocktail. Hãy phân tích cocktail sau và cung cấp thông tin chi tiết bằng Tiếng Việt.
            Tên Cocktail: {name}
            Nguyên liệu: {ingredients}
            Hướng dẫn pha chế: {instructions}
            
            Trả về kết quả chính xác theo định dạng mẫu sau (chỉ trả về chuỗi có định dạng này, không kèm lời dẫn nào khác):
            Hương vị: [Liệt kê tối đa 3 hương vị ngăn cách bằng dấu phẩy, ví dụ: Chua, Ngọt, Thảo mộc]
            Ý nghĩa lịch sử: [Viết 2-3 câu tóm tắt lịch sử, nguồn gốc hoặc ý nghĩa thú vị của ly nước này]
            Loại ly khuyên dùng: [Ví dụ: Ly Martini, Ly Highball, Ly Rock, Ly Coupe]
            Độ cồn: [Chỉ chọn 1 trong: Mocktail (Không cồn), Nhẹ (Low ABV), Vừa (Medium ABV), Mạnh (Strong ABV)]
            """
            
            try:
                res_text = ""
                if model["type"] == "gemini":
                    response = model["model"].generate_content(prompt)
                    res_text = response.text.strip()
                else:
                    # OpenRouter or 9Router
                    import requests
                    import json
                    url = "https://openrouter.ai/api/v1/chat/completions"
                    if model["type"] == "custom":
                        url = f"{model['api_base'].rstrip('/')}/v1/chat/completions"
                    
                    headers = {
                        "Authorization": f"Bearer {model['api_key']}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": model["model"],
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    }
                    if model["type"] == "openrouter":
                        payload["max_tokens"] = 1000
                    
                    resp = requests.post(url, headers=headers, json=payload, timeout=180)
                    if resp.status_code == 200:
                        try:
                            res_data = resp.json()
                        except ValueError:
                            raw = resp.text.strip()
                            import json
                            decoder = json.JSONDecoder()
                            res_data, _ = decoder.raw_decode(raw)
                        res_text = res_data["choices"][0]["message"]["content"].strip()
                    else:
                        raise Exception(f"API Error {resp.status_code}: {resp.text}")
                
                # Parse lines
                flavor_profile = "Cân bằng"
                meaning_and_history = ""
                glassware_recommendation = "Ly Cocktail"
                abv_category = "Vừa (Medium ABV)"
                
                for line in res_text.split('\n'):
                    line = line.strip()
                    if line.startswith("Hương vị:"):
                        flavor_profile = line.split(":", 1)[1].strip()
                    elif line.startswith("Ý nghĩa lịch sử:"):
                        meaning_and_history = line.split(":", 1)[1].strip()
                    elif line.startswith("Loại ly khuyên dùng:"):
                        glassware_recommendation = line.split(":", 1)[1].strip()
                    elif line.startswith("Độ cồn:"):
                        abv_category = line.split(":", 1)[1].strip()
                
                if not meaning_and_history:
                    meaning_and_history = f"Một ly cocktail cổ điển có tên {name}, kết hợp hài hòa giữa các nguyên liệu."
                
                df.at[idx, 'flavor_profile'] = flavor_profile
                df.at[idx, 'meaning_and_history'] = meaning_and_history
                df.at[idx, 'glassware_recommendation'] = glassware_recommendation
                df.at[idx, 'abv_category'] = abv_category
                img = fetch_cocktail_image(name)
                df.at[idx, 'image_url'] = img
                
                print(f"Enriched via LLM: {name} ({idx+1}/30)")
                time.sleep(1.0)  # Rate limiting
                
            except Exception as e:
                print(f"Failed to enrich {name} via Gemini ({e}). Using local fallback.")
                fallback_res = fallback_enrich(row)
                df.at[idx, 'flavor_profile'] = fallback_res[0]
                img = fetch_cocktail_image(name)
                df.at[idx, 'image_url'] = img
                img = fetch_cocktail_image(name)
                df.at[idx, 'image_url'] = img
                df.at[idx, 'meaning_and_history'] = fallback_res[1]
                df.at[idx, 'glassware_recommendation'] = fallback_res[2]
                df.at[idx, 'abv_category'] = fallback_res[3]
                
    # Save the output
    print(f"Saving enriched dataset to {output_csv_path}...")
    df.to_csv(output_csv_path, index=False)
    print("Enrichment complete!")

if __name__ == "__main__":
    main()
