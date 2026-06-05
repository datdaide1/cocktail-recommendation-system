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
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("Warning: GEMINI_API_KEY is not set. Using local fallback rule-based enrichment.")
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.1-flash-lite")
        return model
    except Exception as e:
        print(f"Error configuring Gemini API: {e}. Falling back to rule-based enrichment.")
        return None

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
                response = model.generate_content(prompt)
                res_text = response.text.strip()
                
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
                
                print(f"Enriched via LLM: {name} ({idx+1}/30)")
                time.sleep(1.0)  # Rate limiting
                
            except Exception as e:
                print(f"Failed to enrich {name} via Gemini ({e}). Using local fallback.")
                fallback_res = fallback_enrich(row)
                df.at[idx, 'flavor_profile'] = fallback_res[0]
                df.at[idx, 'meaning_and_history'] = fallback_res[1]
                df.at[idx, 'glassware_recommendation'] = fallback_res[2]
                df.at[idx, 'abv_category'] = fallback_res[3]
                
    # Save the output
    print(f"Saving enriched dataset to {output_csv_path}...")
    df.to_csv(output_csv_path, index=False)
    print("Enrichment complete!")

if __name__ == "__main__":
    main()
