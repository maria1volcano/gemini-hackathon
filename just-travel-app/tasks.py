"""
Background task system with hybrid asyncio/Celery support.
Start with asyncio, migrate to Celery by setting USE_CELERY=true.

Phase 3: Background Task System
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Redis client for task state storage
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
USE_CELERY = os.getenv("USE_CELERY", "false").lower() == "true"

redis_client: Optional[aioredis.Redis] = None


async def init_redis():
    """Initialize Redis connection. Gracefully skips if REDIS_URL not configured."""
    global redis_client

    # Skip if REDIS_URL not set (Cloud Run without Redis)
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.info("ℹ️  REDIS_URL not set - background tasks disabled")
        return

    if redis_client is None:
        redis_client = await aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("✅ Redis client initialized")


async def get_redis() -> aioredis.Redis:
    """Get Redis client, initialize if needed."""
    if redis_client is None:
        await init_redis()
    return redis_client


# ─────────────────────────────────────────────────────────────
# TASK STORAGE (Redis-backed, survives server restart)
# ─────────────────────────────────────────────────────────────

async def save_task_status(task_id: str, status: str, result: Optional[Dict] = None):
    """Save task status to Redis."""
    r = await get_redis()
    task_data = {
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
        "result": result or {}
    }
    await r.setex(
        f"task:{task_id}",
        3600,  # 1 hour TTL
        json.dumps(task_data)
    )


async def get_task_status(task_id: str) -> Optional[Dict]:
    """Get task status from Redis."""
    r = await get_redis()
    data = await r.get(f"task:{task_id}")
    if data:
        return json.loads(data)
    return None


# ─────────────────────────────────────────────────────────────
# ASYNCIO MODE (No Celery)
# ─────────────────────────────────────────────────────────────

if not USE_CELERY:
    logger.info("🚀 Background tasks: AsyncIO mode (no Celery)")

    async def generate_media_background(task_id: str, plan_data: Dict):
        """Generate poster + video in background using asyncio."""
        from agents.creative_director import CreativeDirectorAgent
        from database import get_session
        from database import Itinerary
        from sqlmodel import select

        try:
            await save_task_status(task_id, "generating")
            logger.info(f"🎬 Starting media generation for task {task_id}")

            creative_director = CreativeDirectorAgent()
            result = await creative_director.async_process(plan_data, {})

            await save_task_status(task_id, "completed", result)

            # Try to update database if itinerary was saved with this task_id
            try:
                async for session in get_session():
                    stmt = select(Itinerary).where(Itinerary.media_task_id == task_id)
                    db_result = await session.execute(stmt)
                    itinerary = db_result.scalar_one_or_none()

                    if itinerary:
                        # Store trip poster (main poster) for backward compatibility
                        itinerary.poster_url = result.get("trip_poster_url") or result.get("poster_url", "")
                        itinerary.video_url = result.get("video_url", "")
                        itinerary.media_status = "completed"
                        # Store all creative assets including daily posters in JSON field
                        itinerary.creative_assets = {
                            "trip_poster_url": result.get("trip_poster_url", ""),
                            "daily_posters": result.get("daily_posters", []),
                            "video_url": result.get("video_url", "")
                        }
                        session.add(itinerary)
                        await session.commit()
                        logger.info(f"✅ Updated database for itinerary {itinerary.id} (task {task_id})")
                    else:
                        logger.info(f"ℹ️  No saved itinerary found for task {task_id} (guest user or not saved yet)")
            except Exception as db_error:
                logger.warning(f"⚠️  Could not update database for task {task_id}: {db_error}")
                # Continue even if DB update fails - Redis still has the result

            logger.info(f"✅ Media generation completed for task {task_id}")

        except Exception as e:
            logger.error(f"❌ Media generation failed for task {task_id}: {e}")
            await save_task_status(task_id, "failed", {"error": str(e)})


    def start_background_task(task_id: str, plan_data: Dict):
        """Start asyncio background task."""
        asyncio.create_task(generate_media_background(task_id, plan_data))
        logger.info(f"🚀 Started background task {task_id} (asyncio)")


# ─────────────────────────────────────────────────────────────
# CELERY MODE (Production)
# ─────────────────────────────────────────────────────────────

else:
    from celery import Celery

    celery_app = Celery('just_travel', broker=REDIS_URL, backend=REDIS_URL)

    logger.info("🚀 Background tasks: Celery mode")

    @celery_app.task(bind=True, max_retries=3)
    def generate_media_task(self, task_id: str, plan_data: dict):
        """Generate poster + video using Celery worker."""
        import asyncio
        from agents.creative_director import CreativeDirectorAgent
        from database import get_session
        from database import Itinerary
        from sqlmodel import select

        try:
            # Save initial status
            loop = asyncio.get_event_loop()
            loop.run_until_complete(save_task_status(task_id, "generating"))

            # Generate media
            creative_director = CreativeDirectorAgent()
            result = loop.run_until_complete(
                creative_director.async_process(plan_data, {})
            )

            # Update Redis status
            loop.run_until_complete(save_task_status(task_id, "completed", result))

            # Try to update database if itinerary was saved
            async def update_db():
                try:
                    async for session in get_session():
                        stmt = select(Itinerary).where(Itinerary.media_task_id == task_id)
                        db_result = await session.execute(stmt)
                        itinerary = db_result.scalar_one_or_none()

                        if itinerary:
                            # Store trip poster (main poster) for backward compatibility
                            itinerary.poster_url = result.get("trip_poster_url") or result.get("poster_url", "")
                            itinerary.video_url = result.get("video_url", "")
                            itinerary.media_status = "completed"
                            # Store all creative assets including daily posters
                            itinerary.creative_assets = {
                                "trip_poster_url": result.get("trip_poster_url", ""),
                                "daily_posters": result.get("daily_posters", []),
                                "video_url": result.get("video_url", "")
                            }
                            session.add(itinerary)
                            await session.commit()
                            logger.info(f"✅ Updated database for itinerary {itinerary.id}")
                        else:
                            logger.info(f"ℹ️  No saved itinerary for task {task_id}")
                except Exception as db_error:
                    logger.warning(f"⚠️  DB update failed for task {task_id}: {db_error}")

            loop.run_until_complete(update_db())

            logger.info(f"✅ Celery task completed: {task_id}")
            return result

        except Exception as exc:
            logger.error(f"❌ Celery task failed: {task_id} - {exc}")
            loop.run_until_complete(save_task_status(task_id, "failed", {"error": str(exc)}))
            raise self.retry(exc=exc, countdown=60)


    def start_background_task(task_id: str, plan_data: dict):
        """Start Celery background task."""
        generate_media_task.apply_async(
            args=[task_id, plan_data],
            task_id=task_id
        )
        logger.info(f"🚀 Started Celery task {task_id}")
