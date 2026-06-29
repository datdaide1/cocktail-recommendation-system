import json
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from app.db.redis import redis_client
from app.db.postgres import AsyncSessionLocal
from app.db.models import LiquorPrice, MixologyRule

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # TTL in seconds (1 hour)

async def get_liquor_price_by_name(name: str, session=None) -> List[Dict[str, Any]]:
    """
    Retrieves liquor prices by name, checking Upstash Redis cache first.
    If not cached, queries PostgreSQL, caches the result, and returns it.
    """
    cache_key = f"liquor_price:name:{name}"
    
    # Try cache first
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for key: {cache_key}")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Redis cache read failed for key {cache_key}: {e}")
    
    # Cache miss
    logger.info(f"Cache miss for key: {cache_key}. Querying Supabase...")
    
    is_local_session = False
    if session is None:
        session = AsyncSessionLocal()
        is_local_session = True
        
    try:
        stmt = select(LiquorPrice).where(LiquorPrice.name == name)
        result = await session.execute(stmt)
        records = result.scalars().all()
        
        # Serialize to dict list
        serialized = [
            {
                "id": record.id,
                "name": record.name,
                "category": record.category,
                "size_raw": record.size_raw,
                "size_ml": record.size_ml,
                "price_vnd": record.price_vnd,
                "price_per_ml_vnd": record.price_per_ml_vnd
            }
            for record in records
        ]
        
        # Cache the serialized value in Redis
        try:
            await redis_client.setex(cache_key, CACHE_TTL, json.dumps(serialized))
            logger.info(f"Successfully cached key: {cache_key}")
        except Exception as e:
            logger.warning(f"Redis cache write failed for key {cache_key}: {e}")
            
        return serialized
    finally:
        if is_local_session:
            await session.close()

async def get_liquor_prices_by_category(category: str, session=None) -> List[Dict[str, Any]]:
    """
    Retrieves liquor prices by category, checking Upstash Redis cache first.
    If not cached, queries PostgreSQL, caches the result, and returns it.
    """
    cache_key = f"liquor_prices:category:{category}"
    
    # Try cache first
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for key: {cache_key}")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Redis cache read failed for key {cache_key}: {e}")
        
    # Cache miss
    logger.info(f"Cache miss for key: {cache_key}. Querying Supabase...")
    
    is_local_session = False
    if session is None:
        session = AsyncSessionLocal()
        is_local_session = True
        
    try:
        stmt = select(LiquorPrice).where(LiquorPrice.category == category)
        result = await session.execute(stmt)
        records = result.scalars().all()
        
        serialized = [
            {
                "id": record.id,
                "name": record.name,
                "category": record.category,
                "size_raw": record.size_raw,
                "size_ml": record.size_ml,
                "price_vnd": record.price_vnd,
                "price_per_ml_vnd": record.price_per_ml_vnd
            }
            for record in records
        ]
        
        try:
            await redis_client.setex(cache_key, CACHE_TTL, json.dumps(serialized))
            logger.info(f"Successfully cached key: {cache_key}")
        except Exception as e:
            logger.warning(f"Redis cache write failed for key {cache_key}: {e}")
            
        return serialized
    finally:
        if is_local_session:
            await session.close()

async def get_mixology_rule_by_ingredient(ingredient: str, session=None) -> Optional[Dict[str, Any]]:
    """
    Retrieves mixology rules by ingredient name, checking Upstash Redis cache first.
    If not cached, queries PostgreSQL, caches the result, and returns it.
    """
    cache_key = f"mixology_rule:ingredient:{ingredient}"
    
    # Try cache first
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for key: {cache_key}")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Redis cache read failed for key {cache_key}: {e}")
        
    # Cache miss
    logger.info(f"Cache miss for key: {cache_key}. Querying Supabase...")
    
    is_local_session = False
    if session is None:
        session = AsyncSessionLocal()
        is_local_session = True
        
    try:
        stmt = select(MixologyRule).where(MixologyRule.ingredient == ingredient)
        result = await session.execute(stmt)
        record = result.scalars().first()
        
        if not record:
            return None
            
        serialized = {
            "id": record.id,
            "ingredient": record.ingredient,
            "substitutes": record.substitutes,
            "notes": record.notes
        }
        
        try:
            await redis_client.setex(cache_key, CACHE_TTL, json.dumps(serialized))
            logger.info(f"Successfully cached key: {cache_key}")
        except Exception as e:
            logger.warning(f"Redis cache write failed for key {cache_key}: {e}")
            
        return serialized
    finally:
        if is_local_session:
            await session.close()
