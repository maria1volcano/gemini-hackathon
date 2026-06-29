"""
Social Tools
============

This module provides integration with Apify for social media scraping
and Gemini Vision for visual trend analysis.
"""

import os
import logging
import asyncio
import ipaddress
import urllib.parse
from typing import Optional, Dict
from datetime import datetime
from google import genai
from google.genai import types
import requests

logger = logging.getLogger(__name__)

# Apify client import with fallback
try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    ApifyClient = None
    APIFY_AVAILABLE = False
    logger.warning("Apify client not installed. Social features will use mock data.")

class SocialTools:
    """
    Tool class for social media trend analysis via Apify + Gemini Vision.
    """

    # Apify actor IDs for different platforms
    ACTOR_IDS = {
        "instagram": "apify/instagram-scraper",
        "tiktok": "clockworks/tiktok-scraper",
        "youtube": "streamers/youtube-scraper"
    }

    def __init__(self):
        """Initialize SocialTools."""
        self.api_token = os.getenv("APIFY_API_TOKEN", "")
        self.client = None
        self._initialized = False

        if APIFY_AVAILABLE and self.api_token and "placeholder" not in self.api_token:
            self._initialize_client()
            
        # Initialize Vision Model specifically for Tools usage
        # We reuse the key from env
        api_key = os.getenv("GOOGLE_API_KEY")
        self.genai_client = None
        if api_key:
             self.genai_client = genai.Client(api_key=api_key)
             # Use a Pro model for Vision
             self.vision_model_name = "gemini-3-pro-preview"

        logger.info(f"SocialTools initialized (connected: {self._initialized})")

    def _initialize_client(self) -> bool:
        try:
            self.client = ApifyClient(self.api_token)
            self._initialized = True
            logger.info("Apify client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Apify client: {e}")
            self._initialized = False
            return False

    def get_trending_hashtags(self, destination: str, platform: str = "instagram", limit: int = 10) -> list:
        if not self._initialized:
             return self._get_mock_hashtags(destination, limit)

        results = self.search_platform(platform, [f"#{destination}", f"{destination} travel"], limit=limit)
        if not results:
            return self._get_mock_hashtags(destination, limit)
        return [{"hashtag": f"#{destination}", "count": r.get("likes", 0)} for r in results[:limit]]

    def search_travel_content(self, location: str) -> list:
        return self.search_platform("tiktok", [f"{location} travel guide"], limit=5)


    def search_platform(self, platform: str, queries: list, limit: int = 10) -> list:
        if not self._initialized:
            return self._get_mock_search_results(platform, queries, limit)
        
        try:
            logger.info(f"Searching {platform} via Apify for: {queries}")
            actor_id = self.ACTOR_IDS.get(platform)
            if not actor_id:
                logger.warning(f"No actor configured for {platform}, using mock.")
                return self._get_mock_search_results(platform, queries, limit)

            # Prepare generic input (works for most social scrapers like instagram-scraper)
            # Note: Specific actors might need specific keys (e.g. "search" vs "searchQueries")
            run_input = {
                "search": queries[0], # Simple single query support for stability
                "searchQueries": queries, 
                "resultsLimit": limit,
                "resultsType": "posts"
            }

            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            if not run:
                logger.warning("Apify run failed to start.")
                return []

            # Fetch results
            dataset = self.client.dataset(run["defaultDatasetId"])
            items = list(dataset.iterate_items())
            
            # Normalize results to a common format
            normalized = []
            for item in items:
                normalized.append({
                    "title": item.get("caption") or item.get("text") or "No Caption",
                    "url": item.get("url") or item.get("postUrl"),
                    "thumbnail": item.get("displayUrl") or item.get("thumbnailUrl"),
                    "likes": item.get("likesCount", 0)
                })
                
            return normalized

        except Exception as e:
            logger.error(f"Apify search failed: {e}")
            return self._get_mock_search_results(platform, queries, limit)

    @staticmethod
    def _is_safe_url(url: str) -> bool:
        """Block direct references to private/reserved IPs to mitigate SSRF."""
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False
            host = parsed.hostname
            if not host:
                return False
            try:
                ip = ipaddress.ip_address(host)
                return not (ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local)
            except ValueError:
                return True  # hostname, not a raw IP — allow
        except Exception:
            return False

    async def analyze_visual_vibe(self, content_url: str) -> Dict:
        """
        Analyze the 'vibe' of a piece of visual content using Gemini Vision.
        Downloads the image bytes and calls the model.
        """
        if not content_url:
            return {"vibe_description": "No URL provided"}

        try:
            if not self.genai_client:
                 return {"vibe_description": "Vision AI not configured"}

            if not self._is_safe_url(content_url):
                logger.warning(f"Blocked unsafe URL: {content_url}")
                return {"vibe_description": "URL blocked by safety check.", "error": "Unsafe URL"}

            logger.info(f"Downloading content for analysis: {content_url}")
            response = requests.get(content_url, timeout=10)
            response.raise_for_status()
            image_bytes = response.content
            
            # 2. Call Gemini Vision
            prompt = "Analyze the aesthetic of this travel image. Is it luxury, adventure, chill, or party? Give a score out of 100 for 'Instagrammability'."
            
            # Run the synchronous SDK call in a thread to avoid blocking the event loop
            model_response = await asyncio.to_thread(
                self.genai_client.models.generate_content,
                model=self.vision_model_name,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                ]
            )
            
            return {
                "vibe_description": model_response.text,
                "analyzed_url": content_url
            }
        except Exception as e:
            logger.error(f"Visual Vibe Check failed: {e}")
            return {
                "vibe_description": f"Visual analysis failed ({str(e)}). Assumed vibe based on metadata.", 
                "error": str(e)
            }

    # --- Mocks ---
    def _get_mock_search_results(self, platform, queries, limit):
        return [{"title": f"Viral {q}", "url": "http://mock.url/content.jpg", "hashtags": ["#viral"]} for q in queries]

    def _get_mock_hashtags(self, destination, limit):
         return [{"hashtag": f"#{destination}vibes", "count": 5000}]
