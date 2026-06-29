import logging
import asyncio
from typing import Optional, Dict, Any
from agents.base import BaseAgent

from tools.cypher_tools import CypherTools
from tools.transport_tools import TransportTools
from tools.maps_tools import MapsTools
from tools.amadeus_tools import find_cheapest_dates, flight_price_analysis

logger = logging.getLogger(__name__)

class PathfinderAgent(BaseAgent):
    """
    Agent responsible for destination discovery using LLM and Graph DB.
    """

    def __init__(self):
        super().__init__(name="pathfinder", description="Finds destinations using LLM + Graph", model_type="flash")
        self.cypher_tools = CypherTools()
        self.transport_tools = TransportTools()
        self.maps_tools = MapsTools()
        logger.info("PathfinderAgent initialized with LLM, Transport, and Maps (Google Search via grounding)")

    async def async_process(self, query: str, context: Optional[dict] = None) -> dict:
        """
        Process a destination query using LLM to decide on the tool call.
        """
        context = context or {}
        
        # 1. LLM Reasoning Step
        prompt = f"""
        You are an expert travel graph navigator.
        
        User Query: "{query}"
        User Profile: {context.get("profile", {})}
        
        Your Goal: Determine the best tool to call to answer the user's request.
        
        Available Tools:
        - search_flights(origin, destination, departure_date) -> Use for simple flight queries (Use IATA codes like LHR, JFK).
        - plan_door_to_door(origin_address, dest_address, origin_iata, dest_iata, date) -> Use when precise addresses AND flights are needed.
        - find_by_category(category, location, limit)
        - find_destinations_in_region(region, limit)
        - find_nearby_destinations(location, max_distance_km, limit)
        - find_connected_destinations(location, connection_types, limit)
        - search_destinations(categories, location, budget, limit)

        Note: Google Search grounding is automatically available for current info/general questions.
        
        Output JSON ONLY:
        {{
            "intent": "reasoning about what the user wants",
            "tool_call": "name_of_function",
            "arguments": {{
                "arg1": "value1",
                ...
            }}
        }}
        """
        
        response_text = await self.generate_response(prompt, context=context)
        
        results = []
        intent = "unknown"
        
        try:
            decision = self.parse_json_response(response_text)

            intent = decision.get("intent", "")
            tool_name = decision.get("tool_call")
            args = decision.get("arguments", {})

            logger.info(f"Pathfinder deciding to call: {tool_name} with {args}")

            # 2. Execute Tool — all wrapped in to_thread to avoid blocking the event loop
            if tool_name == "plan_door_to_door":
                results = await self._execute_door_to_door(args)
            elif tool_name == "search_flights":
                # Get base flight results
                flight_results = await asyncio.to_thread(self.transport_tools.search_flights, **args)

                # Enrich with Amadeus intelligence ONLY if flights were found (Phase 1 optimization)
                if isinstance(flight_results, list) and len(flight_results) > 0:
                    logger.info(f"✈️  Found {len(flight_results)} flights, enriching with Amadeus intelligence")
                    amadeus_intel = await self._enrich_with_amadeus_intelligence(
                        origin=args.get("origin", ""),
                        destination=args.get("destination", ""),
                        departure_date=args.get("departure_date")
                    )
                else:
                    logger.info("⏭️  Skipping Amadeus enrichment (no flights found)")
                    amadeus_intel = {"amadeus_intelligence": None}

                # Combine results
                results = {
                    "flights": flight_results,
                    **amadeus_intel
                } if isinstance(flight_results, list) else flight_results
            elif tool_name == "find_by_category":
                results = await asyncio.to_thread(self.cypher_tools.find_by_category, **args)
            elif tool_name == "find_destinations_in_region":
                results = await asyncio.to_thread(self.cypher_tools.find_destinations_in_region, **args)
            elif tool_name == "find_nearby_destinations":
                results = await asyncio.to_thread(self.cypher_tools.find_nearby_destinations, **args)
            elif tool_name == "find_connected_destinations":
                results = await asyncio.to_thread(self.cypher_tools.find_connected_destinations, **args)
            elif tool_name == "search_destinations":
                results = await asyncio.to_thread(self.cypher_tools.search_destinations, **args)
            else:
                results = await asyncio.to_thread(self.cypher_tools.search_destinations, location=args.get("location"))

        except Exception as e:
            logger.error(f"Pathfinder error: {e}")
            results = []

        return {
            "agent": self.name,
            "intent": intent,
            "results": results,
            "result_count": len(results),
            "status": "success" if results else "no_results"
        }

    async def _execute_door_to_door(self, args: dict) -> list:
        """
        Execute multi-modal routing — flight + ground transfers run in parallel.
        """
        origin_addr = args.get("origin_address")
        dest_addr = args.get("dest_address")
        origin_iata = args.get("origin_iata")
        dest_iata = args.get("dest_iata")
        date = args.get("date")

        flight_results, directions_start, directions_end = await asyncio.gather(
            asyncio.to_thread(self.transport_tools.search_flights, origin_iata, dest_iata, date),
            asyncio.to_thread(self.maps_tools.get_directions, origin_addr, f"{origin_iata} Airport"),
            asyncio.to_thread(self.maps_tools.get_directions, f"{dest_iata} Airport", dest_addr),
        )

        return [{
            "type": "door_to_door_plan",
            "segments": [
                {"type": "ground_transfer_start", "details": directions_start},
                {"type": "flight", "details": flight_results},
                {"type": "ground_transfer_end", "details": directions_end}
            ]
        }]

    async def _enrich_with_amadeus_intelligence(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add Amadeus flight intelligence for Optimizer decision-making.

        Returns dict with:
        - cheapest_dates: Alternative dates with better prices
        - price_analysis: Confidence scoring (Great Deal / Fair / High)
        """
        try:
            # Run both Amadeus calls in parallel for speed
            cheapest, analysis = await asyncio.gather(
                find_cheapest_dates(origin, destination, departure_date),
                flight_price_analysis(origin, destination, departure_date or "") if departure_date else asyncio.sleep(0),
                return_exceptions=True
            )

            # Handle exceptions gracefully
            if isinstance(cheapest, Exception):
                logger.warning(f"Cheapest dates failed: {cheapest}")
                cheapest = {}
            if isinstance(analysis, Exception):
                logger.warning(f"Price analysis failed: {analysis}")
                analysis = {}

            return {
                "amadeus_intelligence": {
                    "cheapest_dates": cheapest,
                    "price_analysis": analysis if departure_date else None,
                    "source": "amadeus_api"
                }
            }
        except Exception as e:
            logger.error(f"Amadeus enrichment failed: {e}")
            return {"amadeus_intelligence": None}
