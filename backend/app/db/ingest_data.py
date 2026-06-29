import asyncio
import json
import os
import logging
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from app.db.postgres import engine, AsyncSessionLocal
from app.db.models import Base, Ingredient, LiquorPrice, MixologyRule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ingest_data")

async def ingest_data():
    logger.info("Starting database ingestion process...")

    # 1. Create tables
    async with engine.begin() as conn:
        logger.info("Creating database tables if they do not exist...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully.")

    # Locate paths for cleaned data
    db_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(db_dir))
    cleaned_data_dir = os.path.abspath(os.path.join(backend_dir, "..", "data-pipeline", "data", "cleaned"))

    ingredients_path = os.path.join(cleaned_data_dir, "ingredients.json")
    liquor_prices_path = os.path.join(cleaned_data_dir, "liquor_prices.json")
    mixology_path = os.path.join(cleaned_data_dir, "mixology_data.json")

    logger.info(f"Loading data from directory: {cleaned_data_dir}")

    # Load JSON files
    with open(ingredients_path, "r", encoding="utf-8") as f:
        ingredients_data = json.load(f)
    
    with open(liquor_prices_path, "r", encoding="utf-8") as f:
        liquor_prices_data = json.load(f)
        
    with open(mixology_path, "r", encoding="utf-8") as f:
        mixology_data = json.load(f)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 2. Ingest Ingredients (idempotent upsert)
            logger.info(f"Ingesting {len(ingredients_data)} ingredients...")
            ingredient_vals = [
                {
                    "id": str(item["id"]),
                    "name": item["name"],
                    "description": item.get("description"),
                    "type": item.get("type"),
                    "is_alcoholic": item.get("is_alcoholic", False),
                    "abv": item.get("abv")
                }
                for item in ingredients_data
            ]
            if ingredient_vals:
                stmt_ing = insert(Ingredient).values(ingredient_vals)
                stmt_ing = stmt_ing.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "name": stmt_ing.excluded.name,
                        "description": stmt_ing.excluded.description,
                        "type": stmt_ing.excluded.type,
                        "is_alcoholic": stmt_ing.excluded.is_alcoholic,
                        "abv": stmt_ing.excluded.abv
                    }
                )
                await session.execute(stmt_ing)
            logger.info("Ingredients ingestion completed.")

            # 3. Ingest Liquor Prices (delete and insert for simplicity and idempotency)
            logger.info(f"Ingesting {len(liquor_prices_data)} liquor prices...")
            await session.execute(delete(LiquorPrice))
            
            liquor_price_objects = [
                LiquorPrice(
                    name=item["name"],
                    category=item["category"],
                    size_raw=item["size_raw"],
                    size_ml=item["size_ml"],
                    price_vnd=float(item["price_vnd"]),
                    price_per_ml_vnd=float(item["price_per_ml_vnd"])
                )
                for item in liquor_prices_data
            ]
            session.add_all(liquor_price_objects)
            logger.info("Liquor prices ingestion completed.")

            # 4. Ingest Mixology Rules (idempotent upsert)
            substitutions = mixology_data.get("substitutions", [])
            logger.info(f"Ingesting {len(substitutions)} mixology rules...")
            mixology_vals = [
                {
                    "ingredient": item["ingredient"],
                    "substitutes": item["substitutes"],
                    "notes": item.get("notes")
                }
                for item in substitutions
            ]
            if mixology_vals:
                stmt_mix = insert(MixologyRule).values(mixology_vals)
                stmt_mix = stmt_mix.on_conflict_do_update(
                    index_elements=["ingredient"],
                    set_={
                        "substitutes": stmt_mix.excluded.substitutes,
                        "notes": stmt_mix.excluded.notes
                    }
                )
                await session.execute(stmt_mix)
            logger.info("Mixology rules ingestion completed.")

    logger.info("Database ingestion process completed successfully.")

if __name__ == "__main__":
    asyncio.run(ingest_data())
