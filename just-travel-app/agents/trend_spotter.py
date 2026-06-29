"""
Trend Spotter Agent
===================

This agent uses Gemini 3 to synthesize social media trends from Apify data.
It extracts 'vibes' and trending locations from raw social data.
"""

import logging
import json
from typing import Optional
from agents.base import BaseAgent

from tools.social_tools import SocialTools

logger = logging.getLogger(__name__)

class TrendSpotterAgent(BaseAgent):
    """
    Agent responsible for identifying travel trends using LLM + Social Data.
    """

    def __init__(self):
        super().__init__(name="trend_spotter", description="Analyzes trends using LLM", model_type="flash")
        self.social_tools = SocialTools()
        logger.info("TrendSpotterAgent initialized with LLM")

    async def async_process(self, query: str, context: Optional[dict] = None) -> dict:
        """
        Fetch social data and use LLM to synthesize a 'Trend Report'.
        Implements a Loop Agent pattern: Validates results and retries with broader queries if needed.
        """
        context = context or {}
        original_location = context.get("destination", "Global")
        current_location = original_location
        
        max_retries = 3
        attempt = 0
        final_trends = []
        raw_count = 0
        
        while attempt < max_retries:
            attempt += 1
            logger.info(f"TrendSpotter Attempt {attempt}/{max_retries} for location: {current_location}")

            # 1. Fetch Raw Data
            raw_trends, formatted_posts, is_mock = await self._fetch_social_data(current_location)
            raw_count = len(formatted_posts)

            # Phase 2 optimization: Skip retries if mock data detected
            if is_mock:
                logger.warning(f"⏭️  Mock data detected for {current_location}, skipping retries")
                # Still synthesize trends from mock data (better than nothing)
                final_trends = await self._synthesize_trends(current_location, raw_trends, formatted_posts)
                break

            # 2. Validate Data Presence
            if raw_count == 0:
                if attempt < max_retries:
                    logger.warning(f"No social data found for {current_location}. Broadening search...")
                    current_location = await self._generate_broadening_query(current_location)
                continue

            # 3. LLM Synthesis
            final_trends = await self._synthesize_trends(current_location, raw_trends, formatted_posts)

            # 4. Validate Synthesis Result
            if final_trends:
                logger.info(f"Successfully found {len(final_trends)} trends for {current_location}")
                break
            elif attempt < max_retries:
                logger.warning(f"Synthesis returned empty trends for {current_location}. Retrying...")
                current_location = await self._generate_broadening_query(current_location)
            
        return {
            "agent": self.name,
            "trends": final_trends,
            "raw_count": raw_count,
            "status": "success" if final_trends else "partial_success", # partial if we fell back or found nothing after retries
            "searched_location": current_location
        }

    async def _fetch_social_data(self, location: str):
        """Helper to fetch data from social tools. Returns (trends, posts, is_mock)"""
        try:
            # We start with a broad search based on the query
            raw_trends = self.social_tools.get_trending_hashtags(location)
            formatted_posts = self.social_tools.search_travel_content(location)

            # Phase 2 optimization: Detect mock data to skip retries
            # Mock data contains "MOCK" marker in content
            is_mock = (
                any("MOCK" in str(t).upper() for t in raw_trends[:3] if t) or
                any("MOCK" in str(p).upper() for p in formatted_posts[:3] if p)
            )

            return raw_trends, formatted_posts, is_mock
        except Exception as e:
            logger.error(f"Error fetching social data: {e}")
            return [], [], False

    async def _generate_broadening_query(self, location: str) -> str:
        """Uses LLM to generate a broader search term if the specific one fails."""
        prompt = f"""
        The user is searching for travel trends in '{location}', but we found ZERO social media results.
        We need a BROADER, more popular related location to search instead.
        
        Examples:
        - "SoHo, NY" -> "New York City"
        - "Shibuya Crossing" -> "Tokyo"
        - "Small Village in Italy" -> "Tuscany"
        
        Return ONLY the new location name path. Nothing else.
        """
        response = await self.generate_response(prompt)
        new_location = response.strip().replace('"', '').replace("'", "")
        logger.info(f"Broadening search: '{location}' -> '{new_location}'")
        return new_location

    async def _synthesize_trends(self, location, raw_trends, formatted_posts):
        """Synthesizes the raw data into trends JSON"""
        prompt = f"""
        You are a cool travel trend spotter.
        Location: {location}
        
        Social Media Data:
        {json.dumps(formatted_posts[:10], default=str)}
        
        Trending Hashtags:
        {raw_trends}
        
        Task:
        1. Identify the top 3 specific activities or locations that are "viral" right now.
        2. Give each a "Vibe Score" (1-100).
        3. Explain *why* it's trending (e.g., "Featured in Emily in Paris", "TikTok sunset spot").
        
        Output JSON ONLY:
        {{
            "trends": [
                {{
                    "title": "Name of activity/place",
                    "trend_score": 95,
                    "description": "Why it is cool...",
                    "extracted_locations": ["Location Name"]
                }}
            ],
            "overall_vibe": "Chill", 
            "keywords": ["aesthetic", "coffee"]
        }}
        """
        
        response_text = await self.generate_response(prompt)
        
        try:
            data = self.parse_json_response(response_text)
            return data.get("trends", [])
        except Exception as e:
            logger.error(f"TrendSpotter synthesis error: {e}")
            return []
