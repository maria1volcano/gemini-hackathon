"""
Transport Tools
===============

This module provides integration with the Amadeus API for flight searching
and route planning.
"""

import os
import logging
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Amadeus SDK Import with Fallback
try:
    from amadeus import Client, ResponseError
    AMADEUS_AVAILABLE = True
except ImportError:
    Client = None
    ResponseError = None
    AMADEUS_AVAILABLE = False
    logger.warning("Amadeus SDK not installed. Flight features will use mock data.")

class TransportTools:
    """
    Tool class for transport and flight operations via Amadeus.
    """

    def __init__(self):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
        self.client = None
        self._connected = False

        if AMADEUS_AVAILABLE and self.client_id and "placeholder" not in self.client_id:
            try:
                self.client = Client(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                self._connected = True
                logger.info("Amadeus client initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Amadeus: {e}")

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        max_price: int = None
    ) -> List[Dict]:
        """
        Search for flights between origin and destination.
        
        Args:
            origin: IATA code for origin airport (e.g., "LHR")
            destination: IATA code for destination airport (e.g., "JFK")
            departure_date: Date in YYYY-MM-DD format
            
        Returns:
            List of flight offers
        """
        if not self._connected:
            return self._get_mock_flights(origin, destination, departure_date)

        try:
            # Amadeus API Flight Offer Search
            params = {
                'originLocationCode': origin.upper(),
                'destinationLocationCode': destination.upper(),
                'departureDate': departure_date,
                'adults': adults,
                'max': 5  # Limit results
            }
            
            if max_price:
                params['maxPrice'] = int(max_price)

            response = self.client.shopping.flight_offers_search.get(**params)
            
            # Simple formatting of results
            results = []
            for offer in response.data:
                price = offer['price']['total']
                currency = offer['price']['currency']
                itineraries = offer['itineraries']
                
                segments = []
                for itin in itineraries:
                    for seg in itin['segments']:
                        segments.append({
                            "carrier": seg['carrierCode'],
                            "number": seg['number'],
                            "departure": seg['departure']['at'],
                            "arrival": seg['arrival']['at']
                        })
                
                results.append({
                    "price": f"{price} {currency}",
                    "segments": segments,
                    "id": offer['id']
                })
                
            return results

        except Exception as e:
            logger.error(f"Flight search failed at API level: {e}")
            return self._get_mock_flights(origin, destination, departure_date)

    def _get_mock_flights(self, origin, dest, date) -> List[Dict]:
        """Return mock flight data."""
        return [
            {
                "price": "450.00 EUR",
                "segments": [
                    {
                        "carrier": "AF",
                        "number": "1234",
                        "departure": f"{date}T10:00:00",
                        "arrival": f"{date}T12:00:00"
                    }
                ],
                "id": "mock_1"
            },
            {
                "price": "380.00 EUR",
                "segments": [
                    {
                        "carrier": "BA",
                        "number": "567",
                        "departure": f"{date}T14:30:00",
                        "arrival": f"{date}T16:30:00"
                    }
                ],
                "id": "mock_2"
            }
        ]
