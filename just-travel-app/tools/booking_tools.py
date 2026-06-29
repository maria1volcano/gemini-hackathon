"""
Booking Tools
=============

This module provides integration with Booking.com (via RapidAPI) for
accommodation searching.
"""

import os
import logging
import requests
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class BookingTools:
    """
    Tool class for hotel and accommodation search via Booking.com API.
    """

    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.host = "booking-com15.p.rapidapi.com"
        self._connected = bool(self.api_key and "placeholder" not in self.api_key)

    def search_hotels(
        self,
        location: str,
        checkin_date: str,
        checkout_date: str,
        adults: int = 2,
        rooms: int = 1,
        currency: str = "USD",
        budget_max: Optional[int] = None,
        **kwargs  # Accept and ignore extra params from LLM (e.g., amenities)
    ) -> List[Dict]:
        """
        Search for hotels in a location.
        orchestrates the 2-step process: Resolve Location -> Fetch Hotels.
        Falls back to mock data on ANY failure.
        """
        # Log ignored extra kwargs for debugging
        if kwargs:
            logger.debug(f"Ignoring extra search_hotels params: {list(kwargs.keys())}")

        if not self._connected:
            return self._get_mock_hotels(location)

        try:
            logger.info(f"Resolving location '{location}' via Booking API...")
            dest_id, search_type = self._resolve_location_id(location)
            
            if not dest_id:
                logger.warning(f"Could not resolve location '{location}'. Using mocks.")
                return self._get_mock_hotels(location)
                
            logger.info(f"Fetching hotels for dest_id={dest_id} type={search_type}...")
            hotels = self._fetch_properties(dest_id, search_type, checkin_date, checkout_date, adults, rooms, currency, location, budget_max)
            
            if not hotels:
                logger.warning("No hotels found via API. Using mocks.")
                return self._get_mock_hotels(location)
                
            return hotels
            
        except Exception as e:
            logger.error(f"Booking API failed: {e}. Falling back to mocks.")
            return self._get_mock_hotels(location)

    def _resolve_location_id(self, location: str):
        """Step 1: Get destination ID from location string"""
        url = f"https://{self.host}/api/v1/hotels/searchDestination"
        querystring = {"query": location}
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.host
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and "data" in data and len(data["data"]) > 0:
                first_match = data["data"][0]
                return first_match.get("dest_id"), first_match.get("search_type")
            return None, None
            
        except Exception as e:
            logger.error(f"Location resolution error: {e}")
            raise

    def _fetch_properties(self, dest_id, search_type, checkin, checkout, adults, rooms, currency, location, budget_max=None):
        """Step 2: Get properties list"""
        url = f"https://{self.host}/api/v1/hotels/searchHotels"

        querystring = {
            "dest_id": dest_id,
            "search_type": search_type,
            "arrival_date": checkin,
            "departure_date": checkout,
            "adults": str(adults),
            "room_qty": str(rooms),
            "currency_code": currency,
            "sort_order": "popularity"  # Good default
        }

        # Add budget filter if provided
        if budget_max is not None:
            querystring["price_max"] = str(budget_max)
        
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.host
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Booking-com15 API structure parsing
            # Response typically has { "data": { "hotels": [...] } } or similar
            # We need to adapt based on actual response.
            # Assuming standard rapidapi wrapper format:
            
            hotels = []
            results = data.get("data", {}).get("hotels", [])
            
            if not results and isinstance(data.get("data"), list):
                 # Some wrappers return list directly
                 results = data.get("data")
                 
            # Limit to 5 for the hackathon
            for item in results[:5]:
                property_data = item.get("property", item) # Handle nested or flat
                
                hotels.append({
                    "name": property_data.get("name", "Unknown Hotel"),
                    "price": f"{property_data.get('priceBreakdown', {}).get('grossPrice', {}).get('value', 'N/A')} {currency}",
                    "rating": property_data.get("reviewScore", "N/A"),
                    "address": property_data.get("wishlistName") or location, # Fallback
                    "link": f"https://www.booking.com/hotel/{property_data.get('countryCode', 'us')}/{property_data.get('name', 'hotel').replace(' ', '-').lower()}.html",
                    "thumbnail": property_data.get("photoUrls", [""])[0] if property_data.get("photoUrls") else ""
                })
                
            return hotels
            
        except Exception as e:
            logger.error(f"Property fetch error: {e}")
            raise

    def _get_mock_hotels(self, location: str) -> List[Dict]:
        """Return mock hotel data."""
        return [
            {
                "name": f"Grand Hotel {location}",
                "price": "$200/night",
                "rating": 4.5,
                "address": "City Center",
                "link": "https://booking.com/mock1"
            },
            {
                "name": f"{location} Budget Inn",
                "price": "$85/night",
                "rating": 3.8,
                "address": "Near Station",
                "link": "https://booking.com/mock2"
            },
            {
                "name": "Luxury Resort & Spa",
                "price": "$450/night",
                "rating": 4.9,
                "address": "Seaside",
                "link": "https://booking.com/mock3"
            }
        ]
