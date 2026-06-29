import json
import logging
import asyncio
from typing import Optional
from agents.base import BaseAgent

from tools.maps_tools import MapsTools
from tools.booking_tools import BookingTools

logger = logging.getLogger(__name__)

class ConciergeAgent(BaseAgent):
    """
    Agent responsible for accommodation and dining recommendations using LLM.
    """

    def __init__(self):
        super().__init__(name="concierge", description="Recommends services using LLM + Maps", model_type="pro")
        self.maps_tools = MapsTools()
        self.booking_tools = BookingTools()
        logger.info("ConciergeAgent initialized with LLM and Booking Tools")

    async def async_process(self, query: str, context: Optional[dict] = None) -> dict:
        """
        Process a service query using LLM for intelligent filtering.
        """
        context = context or {}
        profile = context.get("profile", {})
        
        # 1. LLM Reasoning for Filters
        prompt = f"""
        You are a luxury travel concierge.
        User Query: "{query}"
        User Profile: {json.dumps(profile, default=str)}
        
        Task:
        1. Determine if the user wants "accommodation", "restaurant", or "attraction".
        2. Decide which tool to use:
           - "search_hotels" for detailed lodging queries.
           - "search_places" for restaurants, attractions, or general queries.
        3. Extract arguments.
        
        Output JSON ONLY:
        {{
            "service_type": "accommodation",
            "tool_call": "search_hotels", 
            "arguments": {{
                "location": "Paris",
                "checkin_date": "YYYY-MM-DD",
                "checkout_date": "YYYY-MM-DD",
                "budget_max": 200
            }}
        }}
        OR
        {{
            "service_type": "restaurant",
            "tool_call": "search_places",
            "arguments": {{
                 "location": "Paris",
                 "query": "vegan rooftop",
                 "price_levels": [1, 2]
            }}
        }}
        """
        
        response_text = await self.generate_response(prompt, context=context)
        
        results = []
        parsed = {}
        
        try:
            parsed = self.parse_json_response(response_text)

            tool_name = parsed.get("tool_call")
            args = parsed.get("arguments", {})

            logger.info(f"Concierge deciding to call: {tool_name} with {args}")

            if tool_name == "search_hotels":
                results = await asyncio.to_thread(self.booking_tools.search_hotels, **args)
            else:
                results = await asyncio.to_thread(
                    self.maps_tools.search_places,
                    query=args.get("query") or args.get("location"),
                    place_type=args.get("place_type", "restaurant"),
                    location=args.get("location"),
                    price_levels=args.get("price_levels"),
                    open_now=args.get("open_now")
                )

                # Enrich top results in parallel
                # Phase 2 optimization: Reduce enrichment to top 3 (saves 1-2 sec)
                if results:
                    detail_tasks = [
                        asyncio.to_thread(self.maps_tools.get_place_details, place.get("place_id"))
                        for place in results[:3]
                    ]
                    details_list = await asyncio.gather(*detail_tasks)
                    results = [{**place, "details": details} for place, details in zip(results[:3], details_list)]

        except Exception as e:
            logger.error(f"Concierge error: {e}")
            
        return {
            "agent": self.name,
            "service_type": parsed.get("service_type", "unknown"),
            "location": parsed.get("location"),
            "filters_applied": parsed,
            "results": results,
            "result_count": len(results),
            "status": "success" if results else "no_results"
        }
