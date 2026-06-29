"""
Maps Tools
==========

This module provides integration with Google Maps and Places API
for location-based services and place information.

The MapsTools class handles:
- Place search and discovery
- Place details retrieval
- Geocoding and reverse geocoding
- Distance calculations
- Directions and routing

Example Usage:
    tools = MapsTools()
    restaurants = tools.search_places("halal restaurants in Paris", place_type="restaurant")
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Google Maps client import with fallback
try:
    import googlemaps
    GOOGLEMAPS_AVAILABLE = True
except ImportError:
    googlemaps = None
    GOOGLEMAPS_AVAILABLE = False
    logger.warning("Google Maps client not installed. Maps features will use mock data.")


class MapsTools:
    """
    Tool class for Google Maps and Places API operations.

    This class provides high-level methods for searching places,
    getting details, and calculating distances.

    Attributes:
        api_key: Google Maps API key
        client: Google Maps client instance
    """

    # Place type mappings
    PLACE_TYPES = {
        "restaurant": "restaurant",
        "hotel": "lodging",
        "lodging": "lodging",
        "attraction": "tourist_attraction",
        "museum": "museum",
        "park": "park",
        "cafe": "cafe",
        "bar": "bar",
        "shopping": "shopping_mall",
        "transport": "transit_station"
    }

    def __init__(self):
        """Initialize MapsTools with API key from environment."""
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
        self.client = None
        self._initialized = False

        # Initialize client if available
        if GOOGLEMAPS_AVAILABLE and self.api_key and "your_" not in self.api_key:
            self._initialize_client()

        logger.info(f"MapsTools initialized (connected: {self._initialized})")

    def _initialize_client(self) -> bool:
        """
        Initialize the Google Maps client.

        Returns:
            bool: True if initialization successful
        """
        try:
            self.client = googlemaps.Client(key=self.api_key)
            self._initialized = True
            logger.info("Google Maps client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Google Maps client: {e}")
            self._initialized = False
            return False

    def search_places(
        self,
        query: str,
        place_type: Optional[str] = None,
        location: Optional[str] = None,
        price_levels: list = None,
        open_now: bool = False,
        radius: int = 5000
    ) -> list:
        """
        Search for places matching criteria.

        Args:
            query: Search query string
            place_type: Type of place (restaurant, hotel, etc.)
            location: Location name or coordinates
            price_levels: Acceptable price levels (0-4)
            open_now: Filter to only open places
            radius: Search radius in meters

        Returns:
            list: Matching places
        """
        if not self._initialized:
            logger.warning("Google Maps not initialized, returning mock data")
            return self._get_mock_places(query, place_type, location)

        try:
            # Get coordinates for location if it's a string
            coords = None
            if location:
                coords = self._geocode(location)

            # Map place type
            mapped_type = self.PLACE_TYPES.get(place_type, place_type)

            # Build search parameters
            search_params = {
                "query": query,
            }

            if coords:
                search_params["location"] = coords
                search_params["radius"] = radius

            if mapped_type:
                search_params["type"] = mapped_type

            if open_now:
                search_params["open_now"] = True

            # Execute search
            results = self.client.places(**search_params)

            places = results.get("results", [])

            # Filter by price level if specified
            if price_levels:
                places = [
                    p for p in places
                    if p.get("price_level") in price_levels or p.get("price_level") is None
                ]

            return places

        except Exception as e:
            logger.error(f"Places search failed: {e}")
            return self._get_mock_places(query, place_type, location)

    def get_place_details(self, place_id: str) -> dict:
        """
        Get detailed information about a place.

        Args:
            place_id: Google Place ID

        Returns:
            dict: Place details
        """
        if not self._initialized or not place_id:
            return self._get_mock_place_details(place_id)

        try:
            result = self.client.place(
                place_id=place_id,
                fields=[
                    "name", "formatted_address", "formatted_phone_number",
                    "website", "opening_hours", "rating", "reviews",
                    "price_level", "photos", "geometry", "types"
                ]
            )
            return result.get("result", {})

        except Exception as e:
            logger.error(f"Failed to get place details: {e}")
            return self._get_mock_place_details(place_id)

    def geocode(self, address: str) -> Optional[dict]:
        """
        Convert address to coordinates.

        Args:
            address: Address string

        Returns:
            dict: Location with lat/lng or None
        """
        if not self._initialized:
            return {"lat": 48.8566, "lng": 2.3522}  # Default to Paris

        coords = self._geocode(address)
        if coords:
            return {"lat": coords[0], "lng": coords[1]}
        return None

    def _geocode(self, address: str) -> Optional[tuple]:
        """
        Internal geocoding method.

        Args:
            address: Address to geocode

        Returns:
            tuple: (lat, lng) or None
        """
        try:
            results = self.client.geocode(address)
            if results:
                location = results[0]["geometry"]["location"]
                return (location["lat"], location["lng"])
        except Exception as e:
            logger.error(f"Geocoding failed for '{address}': {e}")
        return None

    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Convert coordinates to address.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            str: Formatted address or None
        """
        if not self._initialized:
            return "Sample Address, Sample City"

        try:
            results = self.client.reverse_geocode((lat, lng))
            if results:
                return results[0]["formatted_address"]
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")
        return None

    def calculate_distance(
        self,
        origin: str,
        destination: str,
        mode: str = "driving"
    ) -> Optional[dict]:
        """
        Calculate distance between two points.

        Args:
            origin: Starting point
            destination: End point
            mode: Travel mode (driving, walking, transit, bicycling)

        Returns:
            dict: Distance and duration info
        """
        if not self._initialized:
            return self._get_mock_distance()

        try:
            result = self.client.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode=mode
            )

            if result["rows"]:
                element = result["rows"][0]["elements"][0]
                if element["status"] == "OK":
                    return {
                        "distance": element["distance"],
                        "duration": element["duration"],
                        "mode": mode
                    }

        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")

        return None

    def get_directions(
        self,
        origin: str,
        destination: str,
        waypoints: list = None,
        mode: str = "driving"
    ) -> Optional[list]:
        """
        Get directions between points.

        Args:
            origin: Starting point
            destination: End point
            waypoints: Intermediate stops
            mode: Travel mode

        Returns:
            list: Route steps
        """
        if not self._initialized:
            return self._get_mock_directions()

        try:
            params = {
                "origin": origin,
                "destination": destination,
                "mode": mode
            }

            if waypoints:
                params["waypoints"] = waypoints

            result = self.client.directions(**params)

            if result:
                return result[0].get("legs", [])

        except Exception as e:
            logger.error(f"Directions request failed: {e}")

        return None

    def find_nearby(
        self,
        location: str,
        place_type: str,
        radius: int = 1000,
        keyword: str = None
    ) -> list:
        """
        Find places near a location.

        Args:
            location: Center point
            place_type: Type of places to find
            radius: Search radius in meters
            keyword: Additional keyword filter

        Returns:
            list: Nearby places
        """
        if not self._initialized:
            return self._get_mock_places(keyword or place_type, place_type, location)

        try:
            coords = self._geocode(location)
            if not coords:
                return []

            mapped_type = self.PLACE_TYPES.get(place_type, place_type)

            params = {
                "location": coords,
                "radius": radius,
                "type": mapped_type
            }

            if keyword:
                params["keyword"] = keyword

            result = self.client.places_nearby(**params)
            return result.get("results", [])

        except Exception as e:
            logger.error(f"Nearby search failed: {e}")
            return []

    def get_place_photos(self, place_id: str, max_photos: int = 3) -> list:
        """
        Get photo URLs for a place.

        Args:
            place_id: Google Place ID
            max_photos: Maximum photos to retrieve

        Returns:
            list: Photo URLs
        """
        if not self._initialized:
            return self._get_mock_photos(max_photos)

        try:
            details = self.get_place_details(place_id)
            photos = details.get("photos", [])[:max_photos]

            photo_urls = []
            for photo in photos:
                photo_ref = photo.get("photo_reference")
                if photo_ref:
                    url = f"/api/proxy/photo?ref={photo_ref}"
                    photo_urls.append(url)

            return photo_urls

        except Exception as e:
            logger.error(f"Failed to get photos: {e}")
            return []

    # ==================== Mock Data Methods ====================

    def _get_mock_places(self, query: str, place_type: str, location: str) -> list:
        """Generate mock place results."""
        base_name = place_type.title() if place_type else "Place"
        location_name = location or "City Center"

        return [
            {
                "name": f"{base_name} {i+1} - {query.split()[0] if query else 'Sample'}",
                "place_id": f"mock_place_{i}",
                "rating": 4.5 - (i * 0.2),
                "user_ratings_total": 500 - (i * 50),
                "price_level": (i % 3) + 1,
                "vicinity": f"{100 + i * 10} Main Street, {location_name}",
                "types": [place_type or "establishment", "point_of_interest"],
                "geometry": {
                    "location": {
                        "lat": 48.8566 + (i * 0.01),
                        "lng": 2.3522 + (i * 0.01)
                    }
                },
                "opening_hours": {
                    "open_now": i % 2 == 0
                }
            }
            for i in range(5)
        ]

    def _get_mock_place_details(self, place_id: str) -> dict:
        """Generate mock place details."""
        return {
            "name": "Sample Place",
            "formatted_address": "123 Sample Street, Sample City",
            "formatted_phone_number": "+1 234-567-8900",
            "website": "https://example.com",
            "rating": 4.5,
            "price_level": 2,
            "opening_hours": {
                "open_now": True,
                "weekday_text": [
                    "Monday: 9:00 AM - 10:00 PM",
                    "Tuesday: 9:00 AM - 10:00 PM",
                    "Wednesday: 9:00 AM - 10:00 PM",
                    "Thursday: 9:00 AM - 10:00 PM",
                    "Friday: 9:00 AM - 11:00 PM",
                    "Saturday: 10:00 AM - 11:00 PM",
                    "Sunday: 10:00 AM - 9:00 PM"
                ]
            },
            "reviews": [
                {
                    "rating": 5,
                    "text": "Excellent place! Highly recommended.",
                    "author_name": "John D."
                },
                {
                    "rating": 4,
                    "text": "Great experience, friendly staff.",
                    "author_name": "Sarah M."
                }
            ],
            "photos": []
        }

    def _get_mock_distance(self) -> dict:
        """Generate mock distance data."""
        return {
            "distance": {"text": "5.2 km", "value": 5200},
            "duration": {"text": "15 mins", "value": 900},
            "mode": "driving"
        }

    def _get_mock_directions(self) -> list:
        """Generate mock directions."""
        return [
            {
                "distance": {"text": "5.2 km", "value": 5200},
                "duration": {"text": "15 mins", "value": 900},
                "start_address": "Start Location",
                "end_address": "End Location",
                "steps": [
                    {"instruction": "Head north on Main Street", "distance": {"text": "500 m"}},
                    {"instruction": "Turn right onto 2nd Avenue", "distance": {"text": "1.2 km"}},
                    {"instruction": "Continue straight", "distance": {"text": "2 km"}},
                    {"instruction": "Arrive at destination", "distance": {"text": "0 m"}}
                ]
            }
        ]

    def _get_mock_photos(self, count: int) -> list:
        """Generate mock photo URLs."""
        return [
            f"https://via.placeholder.com/400x300?text=Place+Photo+{i+1}"
            for i in range(count)
        ]
