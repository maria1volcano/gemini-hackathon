"""
Amadeus API Integration - Flight Intelligence & Activities
===========================================================

Provides consultant-level flight recommendations using Amadeus API:
- find_cheapest_dates: Optimal travel dates for price savings
- flight_price_analysis: Price confidence scoring (Great Deal / Fair / High)
- fetch_activities: Bookable tours and experiences

Features:
- LRU cache (15min TTL) for performance
- Request queue (2 req/sec) for rate limiting
- Mock fallback with console logging
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from functools import lru_cache
from collections import deque
import hashlib
import json

logger = logging.getLogger(__name__)

# ─── Configuration ───
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
CACHE_TTL_SECONDS = 900  # 15 minutes
RATE_LIMIT_PER_SECOND = 2
REQUEST_QUEUE_MAX_WAIT = 5  # seconds

# ─── Request Queue (Rate Limiting) ───
class RequestQueue:
    """Thread-safe request queue for rate limiting (2 req/sec)."""

    def __init__(self, rate_limit: int = RATE_LIMIT_PER_SECOND):
        self.rate_limit = rate_limit
        self.requests = deque()
        self.lock = asyncio.Lock()

    async def wait_turn(self):
        """Wait for rate limit slot. Returns True if can proceed."""
        async with self.lock:
            now = datetime.now()
            # Remove requests older than 1 second
            while self.requests and (now - self.requests[0]).total_seconds() > 1:
                self.requests.popleft()

            # Check if under rate limit
            if len(self.requests) < self.rate_limit:
                self.requests.append(now)
                return True

            # Wait for next available slot
            wait_time = 1.0 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self.requests.popleft()
                self.requests.append(datetime.now())
                return True

            return False

request_queue = RequestQueue()

# ─── In-Memory Cache with TTL ───
cache_store: Dict[str, tuple[Any, datetime]] = {}

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()

def get_cached(key: str) -> Optional[Any]:
    """Retrieve cached value if not expired."""
    if key in cache_store:
        value, expiry = cache_store[key]
        if datetime.now() < expiry:
            logger.info(f"Cache HIT: {key[:8]}...")
            return value
        else:
            del cache_store[key]
    return None

def set_cached(key: str, value: Any, ttl_seconds: int = CACHE_TTL_SECONDS):
    """Store value in cache with TTL."""
    expiry = datetime.now() + timedelta(seconds=ttl_seconds)
    cache_store[key] = (value, expiry)
    logger.info(f"Cache SET: {key[:8]}... (TTL: {ttl_seconds}s)")

# ─── Amadeus Client Initialization ───
class AmadeusClient:
    """Wrapper for Amadeus SDK with connection management."""

    def __init__(self):
        self._client = None
        self._connected = False
        self._init_client()

    def _init_client(self):
        """Initialize Amadeus client if credentials are available."""
        if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
            logger.warning("⚠️  Amadeus API keys not found. Using mock data.")
            self._connected = False
            return

        try:
            from amadeus import Client
            self._client = Client(
                client_id=AMADEUS_CLIENT_ID,
                client_secret=AMADEUS_CLIENT_SECRET
            )
            self._connected = True
            logger.info("✅ Amadeus API connected successfully")
        except ImportError:
            logger.error("❌ Amadeus SDK not installed. Run: pip install amadeus")
            self._connected = False
        except Exception as e:
            logger.error(f"❌ Amadeus connection failed: {e}")
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_client(self):
        return self._client

amadeus_client = AmadeusClient()

# ─── Core Functions ───

async def find_cheapest_dates(
    origin: str,
    destination: str,
    departure_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find the cheapest travel dates for a given route.

    Args:
        origin: IATA airport code (e.g., "JFK")
        destination: IATA airport code (e.g., "CDG")
        departure_date: Optional target date (YYYY-MM-DD)

    Returns:
        {
            "cheapest_date": "2024-03-15",
            "price": 450.00,
            "currency": "USD",
            "savings_vs_target": 120.00,  # If departure_date provided
            "alternative_dates": [
                {"date": "2024-03-16", "price": 460.00},
                {"date": "2024-03-17", "price": 470.00}
            ]
        }
    """
    # Generate cache key
    key = cache_key("find_cheapest_dates", origin, destination, departure_date)
    cached = get_cached(key)
    if cached:
        return cached

    # Wait for rate limit
    await request_queue.wait_turn()

    # If Amadeus not connected, use mock data
    if not amadeus_client.is_connected():
        logger.warning(f"🔧 MOCK: find_cheapest_dates({origin} → {destination})")
        result = _mock_cheapest_dates(origin, destination, departure_date)
        set_cached(key, result)
        return result

    try:
        # Real Amadeus API call
        client = amadeus_client.get_client()
        response = client.shopping.flight_dates.get(
            origin=origin,
            destination=destination,
            departureDate=departure_date or (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        )

        data = response.data[0] if response.data else {}
        result = {
            "cheapest_date": data.get("departureDate"),
            "price": float(data.get("price", {}).get("total", 0)),
            "currency": data.get("price", {}).get("currency", "USD"),
            "alternative_dates": []
        }

        set_cached(key, result)
        return result

    except Exception as e:
        logger.error(f"❌ Amadeus API error: {e}. Falling back to mock.")
        result = _mock_cheapest_dates(origin, destination, departure_date)
        set_cached(key, result)
        return result


async def flight_price_analysis(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze flight price confidence (Great Deal / Fair / High).

    Args:
        origin: IATA airport code
        destination: IATA airport code
        departure_date: Departure date (YYYY-MM-DD)
        return_date: Optional return date

    Returns:
        {
            "price": 520.00,
            "currency": "USD",
            "confidence": "Great Deal",  # Great Deal | Fair Price | High Price
            "vs_average": -50.00,  # Negative = below average
            "recommendation": "Book now! This price is $50 lower than average."
        }
    """
    key = cache_key("flight_price_analysis", origin, destination, departure_date, return_date)
    cached = get_cached(key)
    if cached:
        return cached

    await request_queue.wait_turn()

    if not amadeus_client.is_connected():
        logger.warning(f"🔧 MOCK: flight_price_analysis({origin} → {destination})")
        result = _mock_price_analysis(origin, destination, departure_date)
        set_cached(key, result)
        return result

    try:
        client = amadeus_client.get_client()
        # Use Flight Offers Search for price
        response = client.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            returnDate=return_date,
            adults=1,
            max=1
        )

        if not response.data:
            raise ValueError("No flight offers found")

        offer = response.data[0]
        price = float(offer["price"]["total"])

        # Simple confidence logic (can be enhanced with historical data)
        confidence = "Fair Price"
        vs_average = 0.0
        recommendation = "Price is average for this route."

        if price < 400:
            confidence = "Great Deal"
            vs_average = -100.0
            recommendation = "Book now! This is an excellent price."
        elif price > 800:
            confidence = "High Price"
            vs_average = 150.0
            recommendation = "Consider flexible dates for better prices."

        result = {
            "price": price,
            "currency": offer["price"]["currency"],
            "confidence": confidence,
            "vs_average": vs_average,
            "recommendation": recommendation
        }

        set_cached(key, result)
        return result

    except Exception as e:
        logger.error(f"❌ Amadeus API error: {e}. Falling back to mock.")
        result = _mock_price_analysis(origin, destination, departure_date)
        set_cached(key, result)
        return result


async def fetch_activities(
    latitude: float,
    longitude: float,
    radius: int = 10  # km
) -> List[Dict[str, Any]]:
    """
    Fetch bookable activities and tours near coordinates.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        radius: Search radius in kilometers

    Returns:
        [
            {
                "name": "Louvre Museum Skip-the-Line",
                "price": 25.00,
                "currency": "USD",
                "duration": "3 hours",
                "booking_url": "https://...",
                "image_url": "https://...",
                "rating": 4.8
            }
        ]
    """
    key = cache_key("fetch_activities", latitude, longitude, radius)
    cached = get_cached(key)
    if cached:
        return cached

    await request_queue.wait_turn()

    if not amadeus_client.is_connected():
        logger.warning(f"🔧 MOCK: fetch_activities({latitude}, {longitude})")
        result = _mock_activities(latitude, longitude)
        set_cached(key, result)
        return result

    try:
        client = amadeus_client.get_client()
        response = client.shopping.activities.get(
            latitude=latitude,
            longitude=longitude,
            radius=radius
        )

        activities = []
        for activity in response.data[:5]:  # Limit to top 5
            activities.append({
                "name": activity.get("name", "Activity"),
                "price": float(activity.get("price", {}).get("amount", 0)),
                "currency": activity.get("price", {}).get("currencyCode", "USD"),
                "duration": activity.get("duration", "Unknown"),
                "booking_url": activity.get("bookingLink", ""),
                "image_url": activity.get("pictures", [{}])[0].get("url", ""),
                "rating": float(activity.get("rating", 0))
            })

        set_cached(key, activities)
        return activities

    except Exception as e:
        logger.error(f"❌ Amadeus API error: {e}. Falling back to mock.")
        result = _mock_activities(latitude, longitude)
        set_cached(key, result)
        return result


# ─── Mock Data Functions ───

def _mock_cheapest_dates(origin: str, dest: str, target_date: Optional[str]) -> Dict:
    """Generate realistic mock data for cheapest dates."""
    base_price = 450.0
    return {
        "cheapest_date": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
        "price": base_price,
        "currency": "USD",
        "savings_vs_target": 120.0 if target_date else None,
        "alternative_dates": [
            {"date": (datetime.now() + timedelta(days=16)).strftime("%Y-%m-%d"), "price": base_price + 10},
            {"date": (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d"), "price": base_price + 20}
        ]
    }

def _mock_price_analysis(origin: str, dest: str, date: str) -> Dict:
    """Generate realistic mock price analysis."""
    return {
        "price": 520.0,
        "currency": "USD",
        "confidence": "Great Deal",
        "vs_average": -50.0,
        "recommendation": "Book now! This price is $50 lower than average."
    }

def _mock_activities(lat: float, lon: float) -> List[Dict]:
    """Generate realistic mock activities."""
    return [
        {
            "name": "Museum Skip-the-Line Ticket",
            "price": 25.0,
            "currency": "USD",
            "duration": "3 hours",
            "booking_url": "https://example.com/book",
            "image_url": "https://via.placeholder.com/300x200",
            "rating": 4.8
        },
        {
            "name": "City Walking Tour",
            "price": 15.0,
            "currency": "USD",
            "duration": "2 hours",
            "booking_url": "https://example.com/book",
            "image_url": "https://via.placeholder.com/300x200",
            "rating": 4.6
        }
    ]
