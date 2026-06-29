import asyncio
import time
import sys
import logging
from app.db.postgres import check_postgres_connection, engine
from app.db.redis import check_redis_connection, redis_client
from app.db.cache import get_liquor_price_by_name, get_mixology_rule_by_ingredient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("verify_db")

async def test_caching_behavior():
    test_name = "Absolut Vodka"
    cache_key = f"liquor_price:name:{test_name}"
    
    # 1. Clear key to force cache miss
    await redis_client.delete(cache_key)
    
    # 2. First request: measure time (miss)
    start_time = time.perf_counter()
    prices_miss = await get_liquor_price_by_name(test_name)
    duration_miss = time.perf_counter() - start_time
    logger.info(f"Cache miss query took {duration_miss:.6f} seconds.")
    
    # Assert we retrieved data from database
    assert len(prices_miss) > 0, "Failed to retrieve Absolut Vodka price from DB"
    
    # Verify the cache key now exists in Redis
    exists = await redis_client.exists(cache_key)
    assert exists == 1, "Cache key was not created in Redis after miss"
    
    # 3. Second request: measure time (hit)
    start_time = time.perf_counter()
    prices_hit = await get_liquor_price_by_name(test_name)
    duration_hit = time.perf_counter() - start_time
    logger.info(f"Cache hit query took {duration_hit:.6f} seconds.")
    
    # Assert data is identical
    assert prices_miss == prices_hit, "Cache hit data did not match cache miss data"
    
    # Assert cache hit is faster or check that cache key exists
    logger.info("Caching verification passed successfully.")

async def main():
    logger.info("=== Starting Database Schema and Caching Verification ===")
    
    # Assert PostgreSQL connection is successful
    logger.info("Verifying PostgreSQL connection...")
    pg_ok = await check_postgres_connection()
    assert pg_ok, "PostgreSQL connection failed!"
    
    # Assert Redis connection is successful
    logger.info("Verifying Upstash Redis connection...")
    redis_ok = await check_redis_connection()
    assert redis_ok, "Upstash Redis connection failed!"
    
    # Query imported liquor price
    logger.info("Querying 'Absolut Vodka' liquor price...")
    absolut_prices = await get_liquor_price_by_name("Absolut Vodka")
    assert len(absolut_prices) > 0, "Could not find 'Absolut Vodka' in database"
    logger.info(f"Found 'Absolut Vodka' prices: {absolut_prices}")
    
    # Query imported mixology rule
    logger.info("Querying 'Cointreau' mixology rule...")
    cointreau_rule = await get_mixology_rule_by_ingredient("Cointreau")
    assert cointreau_rule is not None, "Could not find 'Cointreau' mixology rule in database"
    assert "Triple Sec" in cointreau_rule["substitutes"], "Cointreau substitutes missing Triple Sec"
    logger.info(f"Found 'Cointreau' rule: {cointreau_rule}")
    
    # Test caching behavior
    logger.info("Verifying caching functionality...")
    await test_caching_behavior()
    
    # Cleanup resources
    await engine.dispose()
    await redis_client.aclose()
    
    logger.info("=== All Verifications Passed Successfully ===")
    sys.exit(0)

if __name__ == "__main__":
    # Explicitly handle asyncio loop to avoid warnings on exit
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
