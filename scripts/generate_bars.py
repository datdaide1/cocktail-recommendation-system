import pandas as pd
import random

cities = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Nha Trang"]
districts_hn = ["Hoàn Kiếm", "Ba Đình", "Tây Hồ", "Đống Đa", "Hai Bà Trưng"]
districts_hcm = ["Quận 1", "Quận 2", "Quận 3", "Bình Thạnh", "Phú Nhuận"]
styles = ["Speakeasy", "Modern Lounge", "Classic Pub", "Rooftop Bar", "Jazz Club", "Dive Bar"]
price_ranges = ["$", "$$", "$$$", "$$$$"]
vibes = [
    "A hidden gem with a mysterious and intimate atmosphere.",
    "Lively and energetic, perfect for a night out with friends.",
    "Sophisticated and elegant, ideal for romantic dates.",
    "A casual spot with great music and affordable drinks.",
    "Exclusive and luxurious, offering breathtaking city views.",
    "Cozy and rustic, featuring live acoustic performances.",
    "A vibrant mix of modern art and exceptional mixology.",
    "Quiet and relaxing, the best place to unwind after work."
]
signature_ingredients = ["Gin", "Whiskey", "Rum", "Vodka", "Tequila", "Mezcal", "Matcha", "Lotus", "Chili", "Coffee"]

bar_names = [
    "The Alchemist", "Midnight Bloom", "Neon Dreams", "Velvet Room", "Copper & Oak", 
    "The Blind Tiger", "Silent Siren", "Crimson Lounge", "Sapphire Sky", "Golden Hour",
    "Iron Fist Pub", "The Local", "Urban Myth", "Echo Chamber", "Nomad's Rest",
    "Whispering Winds", "Shadow Play", "Lunar Eclipse", "Solar Flare", "Starlight",
    "The Boathouse", "Harbor View", "Sky High", "Cloud 9", "The Vault",
    "Secret Garden", "Hidden Door", "Lost & Found", "The Observatory", "Paradox",
    "Enigma", "Mirage", "Oasis", "The Catalyst", "Axiom",
    "The Nexus", "Quantum", "Pulse", "Rhythm & Blues", "Jazz Corner",
    "The Brass Note", "Melody Lounge", "Harmonic", "Tempo", "Cadence",
    "The Rusty Nail", "Broken Barrel", "Tipsy Fox", "Sober Monkey", "Laughing Buddha",
    "The Drunken Sailor", "Mermaid's Tale", "Kraken's Lair", "The Pearl", "Ocean's Edge",
    "Sunset Boulevard", "Midnight Express", "Night Owl", "Early Bird", "The Roost",
    "The Nest", "Eagle's Eye", "Hawk's View", "Falcon's Dive", "Raven's Call",
    "The Crow's Nest", "Black Cat", "White Rabbit", "Red Fox", "Blue Bear",
    "The Green Dragon", "Golden Lion", "Silver Wolf", "Bronze Bull", "Iron Horse"
]

data = []
for name in bar_names:
    city = random.choice(cities)
    if city == "Hà Nội":
        district = random.choice(districts_hn)
    elif city == "Hồ Chí Minh":
        district = random.choice(districts_hcm)
    else:
        district = "Trung Tâm"
    
    style = random.choice(styles)
    price = random.choice(price_ranges)
    vibe = random.choice(vibes)
    signature = f"{random.choice(signature_ingredients)} {random.choice(['Smash', 'Sour', 'Fizz', 'Martini', 'Old Fashioned', 'Mule'])}"
    
    data.append({
        "name": name,
        "address": f"{random.randint(1, 200)} {random.choice(['Lê Lợi', 'Nguyễn Huệ', 'Trần Hưng Đạo', 'Hai Bà Trưng', 'Lý Tự Trọng', 'Pasteur'])}",
        "district": district,
        "city": city,
        "style": style,
        "price_range": price,
        "vibe_description": vibe,
        "signature_cocktail": signature
    })

df = pd.DataFrame(data)
df.to_csv("e:/RECOMMENDATION-SYSTEM/cocktail-recommendation-system/data/bars_vietnam.csv", index=False)
print(f"Generated {len(df)} bars successfully.")
