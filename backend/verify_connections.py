import asyncio
import logging
from app.db.postgres import check_postgres_connection, engine
from app.db.redis import check_redis_connection, redis_client
from app.db.qdrant import check_qdrant_connection, qdrant_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("verify_connections")

async def main():
    logger.info("=== Starting Database Connections Verification ===")
    
    # Check PostgreSQL
    logger.info("Checking PostgreSQL (Supabase) connection...")
    pg_ok = await check_postgres_connection()
    
    # Check Redis
    logger.info("Checking Redis (Upstash) connection...")
    redis_ok = await check_redis_connection()
    
    # Check Qdrant
    logger.info("Checking Qdrant Cloud connection...")
    qdrant_ok = await check_qdrant_connection()
    
    logger.info("=== Verification Summary ===")
    logger.info(f"PostgreSQL : {'[OK]' if pg_ok else '[FAILED]'}")
    logger.info(f"Redis      : {'[OK]' if redis_ok else '[FAILED]'}")
    logger.info(f"Qdrant     : {'[OK]' if qdrant_ok else '[FAILED]'}")

    # Cleanup resources
    await engine.dispose()
    await redis_client.aclose()
    await qdrant_client.close()

if __name__ == "__main__":
    # Explicitly handle asyncio loop to avoid warnings on exit
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
