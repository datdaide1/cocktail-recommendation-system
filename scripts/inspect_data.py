import pandas as pd
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

df = pd.read_csv('data/enriched_cocktails.csv', encoding='utf-8')

print("=== COCKTAILS ===")

for col in ['category', 'flavor_profile', 'abv_category', 'alcoholic', 'glassType']:
    vals = df[col].dropna().unique().tolist()
    print(f"\n{col} ({len(vals)} unique):")
    for v in vals[:25]:
        print(f"  - {v}")

# Extract base spirits
all_ingredients = []
for ing_str in df['ingredients'].dropna():
    try:
        ing_list = eval(ing_str)
        if isinstance(ing_list, list):
            all_ingredients.extend([i.strip() for i in ing_list])
    except:
        pass

from collections import Counter
top_ingredients = Counter(all_ingredients).most_common(30)
print("\nTop 30 Ingredients:")
for name, count in top_ingredients:
    print(f"  - {name}: {count}")

# Bars
print("\n=== BARS ===")
df2 = pd.read_csv('data/bars_vietnam.csv', encoding='utf-8')
print("Columns:", df2.columns.tolist())
for col in ['city', 'district', 'style', 'price_range']:
    vals = df2[col].dropna().unique().tolist()
    print(f"\n{col} ({len(vals)} unique):")
    for v in vals:
        print(f"  - {v}")
