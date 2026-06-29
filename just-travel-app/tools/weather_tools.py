"""
Weather Tools
=============

Provides weather forecast data via OpenWeatherMap API.
Falls back to realistic mock data when the API key is missing or invalid.

Example Usage:
    tools = WeatherTools()
    forecast = tools.get_forecast("Paris", days=5)
"""

import os
import logging
from typing import Optional
from cachetools import TTLCache

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Weather forecast cache (15 min TTL, max 500 cities)
weather_cache = TTLCache(maxsize=500, ttl=900)

# Activity categories that are weather-sensitive
OUTDOOR_ACTIVITY_TYPES = {"hiking", "swimming", "cycling", "outdoor", "beach", "camping", "skiing"}


class WeatherTools:
    """
    Tool class for OpenWeatherMap forecast queries.

    Attributes:
        api_key: OpenWeatherMap API key
        _connected: True when a valid key is present
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self):
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
        self._connected = bool(
            REQUESTS_AVAILABLE
            and self.api_key
            and "your_" not in self.api_key
        )
        logger.info(f"WeatherTools initialized (connected: {self._connected})")

    # ── Public API ──────────────────────────────────────────────

    def get_forecast(self, city: str, days: int = 5) -> dict:
        """
        Return a multi-day forecast for *city*.

        Args:
            city: City name (optionally with country code, e.g. "Paris,FR")
            days: Number of days to forecast (1-5; capped at 5 for free tier)

        Returns:
            dict with keys:
                city        – resolved city name
                country     – two-letter country code
                forecasts   – list of daily dicts (see _parse_daily)
        """
        days = min(max(days, 1), 5)

        # Check cache first (Phase 1 optimization)
        cache_key = f"forecast:{city.lower()}:{days}"
        if cache_key in weather_cache:
            logger.info(f"⚡ Weather cache HIT for {city} ({days} days)")
            return weather_cache[cache_key]

        if not self._connected:
            result = self._mock_forecast(city, days)
            weather_cache[cache_key] = result
            return result

        try:
            # 5-day / 3-hour endpoint covers up to 5 days
            resp = requests.get(
                f"{self.BASE_URL}/forecast",
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                    "cnt": days * 8,  # 8 readings per day (every 3 h)
                },
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json()
            result = self._parse_forecast(data, days)

            # Cache successful result (Phase 1 optimization)
            weather_cache[cache_key] = result
            logger.info(f"💾 Cached weather for {city} ({days} days)")
            return result

        except Exception as e:
            logger.warning(f"OpenWeatherMap request failed ({city}): {e}")
            result = self._mock_forecast(city, days)
            weather_cache[cache_key] = result  # Cache mock too
            return result

    def get_current(self, city: str) -> dict:
        """
        Return current weather for *city*.

        Returns:
            dict: { city, country, temp_c, feels_like_c, condition, humidity, wind_kmh, icon }
        """
        if not self._connected:
            return self._mock_current(city)

        try:
            resp = requests.get(
                f"{self.BASE_URL}/weather",
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                },
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "city": data.get("name", city),
                "country": data.get("sys", {}).get("country", ""),
                "temp_c": round(data["main"]["temp"], 1),
                "feels_like_c": round(data["main"]["feels_like"], 1),
                "condition": data["weather"][0]["description"].capitalize(),
                "humidity": data["main"]["humidity"],
                "wind_kmh": round(data["wind"]["speed"] * 3.6, 1),
                "icon": data["weather"][0]["icon"],
            }

        except Exception as e:
            logger.warning(f"Current-weather request failed ({city}): {e}")
            return self._mock_current(city)

    @staticmethod
    def is_outdoor_activity(activity_type: str) -> bool:
        """Check whether an activity type should be weather-gated."""
        return activity_type.lower().strip() in OUTDOOR_ACTIVITY_TYPES

    @staticmethod
    def weather_advisory(condition: str, temp_c: float) -> Optional[str]:
        """
        Return a short advisory string if conditions warrant one, else None.
        """
        cond = condition.lower()
        if "thunder" in cond:
            return "⚠️ Thunderstorms expected – consider indoor alternatives."
        if "snow" in cond and temp_c < 0:
            return "❄️ Heavy snow & sub-zero temps – dress in layers, check transport."
        if "rain" in cond or "drizzle" in cond:
            return "🌧️ Rain in the forecast – bring an umbrella."
        if temp_c > 35:
            return "🔥 Extreme heat – stay hydrated and seek shade mid-day."
        if temp_c < -10:
            return "🥶 Extreme cold – limit outdoor exposure."
        return None

    # ── Parsing ─────────────────────────────────────────────────

    @staticmethod
    def _parse_forecast(data: dict, days: int) -> dict:
        """Aggregate 3-hour readings into daily summaries."""
        city = data.get("city", {}).get("name", "Unknown")
        country = data.get("city", {}).get("country", "")
        readings = data.get("list", [])

        # Group by date
        from collections import defaultdict
        daily: dict[str, list] = defaultdict(list)
        for r in readings:
            date = r["dt_txt"].split(" ")[0]
            daily[date].append(r)

        forecasts = []
        for date in sorted(daily.keys())[:days]:
            entries = daily[date]
            temps = [e["main"]["temp"] for e in entries]
            conditions = [e["weather"][0]["description"] for e in entries]
            # Pick the most common condition (rough "mode")
            condition = max(set(conditions), key=conditions.count).capitalize()
            forecasts.append({
                "date": date,
                "temp_min_c": round(min(temps), 1),
                "temp_max_c": round(max(temps), 1),
                "condition": condition,
                "humidity_avg": round(sum(e["main"]["humidity"] for e in entries) / len(entries)),
                "wind_kmh": round(max(e["wind"]["speed"] for e in entries) * 3.6, 1),
                "advisory": WeatherTools.weather_advisory(condition, max(temps)),
            })

        return {"city": city, "country": country, "forecasts": forecasts}

    # ── Mock data ───────────────────────────────────────────────

    @staticmethod
    def _mock_forecast(city: str, days: int) -> dict:
        """Deterministic mock forecast based on city name hash."""
        import hashlib
        seed = int(hashlib.md5(city.lower().encode()).hexdigest(), 16)
        conditions = ["Sunny", "Partly cloudy", "Cloudy", "Light rain", "Overcast"]
        forecasts = []
        for i in range(days):
            cond_idx = (seed + i) % len(conditions)
            temp_base = 18 + (seed % 12) - i  # slight daily variation
            temp_min  = round(temp_base - 4 + (i % 3), 1)
            temp_max  = round(temp_base + 5 - (i % 2), 1)
            condition = conditions[cond_idx]
            forecasts.append({
                "date": f"2026-02-{6 + i:02d}",
                "temp_min_c": temp_min,
                "temp_max_c": temp_max,
                "condition": condition,
                "humidity_avg": 55 + (seed + i) % 30,
                "wind_kmh": 8 + (seed + i) % 20,
                "advisory": WeatherTools.weather_advisory(condition, temp_max),
            })
        return {"city": city, "country": "XX", "forecasts": forecasts}

    @staticmethod
    def _mock_current(city: str) -> dict:
        import hashlib
        seed = int(hashlib.md5(city.lower().encode()).hexdigest(), 16)
        conditions = ["Sunny", "Partly cloudy", "Cloudy", "Light rain"]
        return {
            "city": city,
            "country": "XX",
            "temp_c": round(15 + (seed % 15), 1),
            "feels_like_c": round(14 + (seed % 13), 1),
            "condition": conditions[seed % len(conditions)],
            "humidity": 50 + seed % 30,
            "wind_kmh": round(5 + seed % 20, 1),
            "icon": "01d",
        }
