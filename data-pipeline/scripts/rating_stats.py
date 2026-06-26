import os
import json

venues_path = os.path.join(os.path.dirname(__file__), "../../../crawled-data/venues.json")
with open(venues_path, 'r', encoding='utf-8') as f:
    venues = json.load(f)

ratings = [v['rating'] for v in venues if v.get('rating') is not None]
avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
print(f"Average rating: {avg_rating:.2f}")
print(f"Max rating: {max(ratings) if ratings else 0.0}")
print(f"Min rating: {min(ratings) if ratings else 0.0}")
