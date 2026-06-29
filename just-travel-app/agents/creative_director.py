import logging
import asyncio
from typing import Optional, Dict, List
from agents.base import BaseAgent
from tools.creative_tools import CreativeTools

logger = logging.getLogger(__name__)

# Maximum number of daily posters to generate (even for longer trips)
MAX_DAILY_POSTERS = 5


class CreativeDirectorAgent(BaseAgent):
    """
    Agent responsible for generating visual assets ("The Commercial") for the trip.

    Generates:
    - 1 trip overview poster
    - Up to 5 daily posters (one per day, max 5)
    - 1 promotional video (8 seconds)
    """

    def __init__(self):
        super().__init__(name="creative_director", description="Generates visual previews", model_type="pro")
        self.creative_tools = CreativeTools()
        logger.info("CreativeDirectorAgent initialized.")

    def _extract_destination(self, plan_data: Dict, context: Dict) -> str:
        """Extract the main destination from plan data or context."""
        # PRIORITY 1: Direct destination in context (from main.py pipeline)
        if context.get("destination"):
            return context["destination"]

        # PRIORITY 2: Profile destination (from user preferences)
        profile = context.get("profile", {})
        if profile.get("destination"):
            return profile["destination"]

        # PRIORITY 3: Try from plan data trip_title
        if plan_data.get("trip_title"):
            title = plan_data["trip_title"]
            # Common patterns: "5 Days in Paris", "Paris Adventure", "Exploring Tokyo"
            for word in ["in ", "to ", "Exploring ", "Discovering "]:
                if word in title:
                    return title.split(word)[-1].strip()

        # PRIORITY 4: Try from accommodation address
        accommodation = plan_data.get("accommodation", {})
        if accommodation.get("address"):
            # Extract city from address (usually last part before country)
            parts = accommodation["address"].split(",")
            if len(parts) >= 2:
                return parts[-2].strip()

        # PRIORITY 5: Try from flights arrival airport
        flights = plan_data.get("flights", {})
        if flights.get("outbound", {}).get("arrival_airport"):
            return flights["outbound"]["arrival_airport"]

        # Fallback
        return "an amazing destination"

    def _extract_landmarks(self, daily_itinerary: List[Dict]) -> List[str]:
        """Extract key landmarks and attractions from the itinerary."""
        landmarks = []
        for day in daily_itinerary:
            # From key_locations
            landmarks.extend(day.get("key_locations", []))

            # From time_slots - extract activity names
            for slot in day.get("time_slots", []):
                activity = slot.get("activity", {})
                if isinstance(activity, dict):
                    name = activity.get("name", "")
                    activity_type = activity.get("type", "")
                    # Filter for visually interesting activities
                    if activity_type in ["museum", "landmark", "attraction", "park", "monument", "beach", "viewpoint"]:
                        if name and name not in landmarks:
                            landmarks.append(name)
                    elif name and "check" not in name.lower() and "transfer" not in name.lower():
                        if name not in landmarks:
                            landmarks.append(name)

        # Return unique landmarks, limited to top 10
        return list(dict.fromkeys(landmarks))[:10]

    async def async_process(self, plan_data: Dict, context: Optional[dict] = None) -> Dict:
        """
        Analyze the itinerary and generate daily posters, trip poster, and video.
        Uses actual trip details (destination, landmarks, activities) for relevant images.
        """
        logger.info("Creative Director starting production...")

        context = context or {}

        # Extract itinerary data from Optimizer output
        daily_itinerary = plan_data.get("daily_itinerary", [])
        trip_title = plan_data.get("trip_title", "Your Amazing Trip")
        trip_visual_theme = plan_data.get("trip_visual_theme", "Adventure awaits")
        itinerary_summary = plan_data.get("summary", "")

        # Extract destination and key landmarks for more specific prompts
        destination = self._extract_destination(plan_data, context)
        key_landmarks = self._extract_landmarks(daily_itinerary)

        logger.info(f"Generating visuals for: {destination}")
        logger.info(f"Key landmarks: {key_landmarks[:5]}")

        # Check for user uploads
        uploaded_file = context.get("uploaded_file")

        # Limit daily posters to MAX_DAILY_POSTERS
        days_to_render = daily_itinerary[:MAX_DAILY_POSTERS]
        num_days = len(days_to_render)

        logger.info(f"Generating {num_days} daily posters + 1 trip poster + 1 video")

        # 1. Generate prompts for daily posters with SPECIFIC location details
        daily_poster_prompts = []
        for day in days_to_render:
            day_num = day.get("day_number", 1)
            theme = day.get("theme", "Exploration")
            highlight = day.get("daily_highlight", "")
            visual_theme = day.get("visual_theme", "Vibrant and exciting")
            day_locations = day.get("key_locations", [])

            # Build specific prompt with actual location names
            location_str = ", ".join(day_locations[:3]) if day_locations else destination

            prompt = f"""
            Stunning travel photograph of {destination}.
            Day {day_num} theme: {theme}

            Featured locations: {location_str}
            Highlight moment: {highlight if highlight else f'exploring {destination}'}
            Visual mood: {visual_theme}

            Style: Ultra high-resolution travel photography, golden hour lighting,
            cinematic composition, National Geographic quality,
            showing the real architecture and landscape of {destination}

            IMPORTANT: This must look like an ACTUAL photograph of {destination},
            showing recognizable landmarks and authentic local atmosphere.
            """
            daily_poster_prompts.append((day_num, prompt.strip()))

        # 2. Generate trip overview poster prompt with SPECIFIC destination details
        landmarks_str = ", ".join(key_landmarks[:5]) if key_landmarks else destination

        trip_poster_prompt = f"""
        Breathtaking cinematic travel poster featuring {destination}.

        Title: "{trip_title}"
        Theme: {trip_visual_theme}

        Must include iconic elements of {destination}:
        Key landmarks to feature: {landmarks_str}

        Trip summary: {itinerary_summary[:300] if itinerary_summary else f'An unforgettable journey through {destination}'}

        Style: Epic wide-angle shot, professional travel photography, dramatic lighting,
        captures the essence of {destination} in one breathtaking image.
        Should look like a real photograph taken in {destination}, showing actual
        architecture, landscape, and cultural elements authentic to this location.

        IMPORTANT: Generate an image that clearly represents {destination} with its
        famous landmarks, architecture style, and atmosphere.
        """

        # 3. Generate all posters in parallel
        poster_tasks = []

        # Daily poster tasks
        for day_num, prompt in daily_poster_prompts:
            poster_tasks.append(self.creative_tools.generate_image(prompt))

        # Trip poster task (added last)
        poster_tasks.append(self.creative_tools.generate_image(trip_poster_prompt.strip()))

        logger.info(f"Starting parallel generation of {len(poster_tasks)} posters for {destination}...")
        poster_results = await asyncio.gather(*poster_tasks, return_exceptions=True)

        # 4. Parse poster results
        daily_posters: List[Dict] = []
        for i, (day_num, _) in enumerate(daily_poster_prompts):
            result = poster_results[i]
            if isinstance(result, Exception):
                logger.error(f"Day {day_num} poster failed: {result}")
                url = ""
            else:
                url = result or ""
            daily_posters.append({"day": day_num, "poster_url": url})

        # Trip poster is the last result
        trip_poster_result = poster_results[-1] if poster_results else None
        if isinstance(trip_poster_result, Exception):
            logger.error(f"Trip poster failed: {trip_poster_result}")
            trip_poster_url = ""
        else:
            trip_poster_url = trip_poster_result or ""

        # 5. Generate video using trip poster as input with SPECIFIC destination context
        video_prompt = f"""
        Cinematic 8-second travel advertisement showcasing {destination}.

        Title: "{trip_title}"
        Mood: {trip_visual_theme}

        The video should capture the essence of {destination} with:
        - Iconic landmarks: {landmarks_str}
        - Local atmosphere and culture
        - Beautiful scenery authentic to {destination}

        Style: Smooth drone shots, golden hour lighting, professional travel commercial quality,
        showing the real beauty and character of {destination}.
        """

        video_url = ""
        try:
            # Use trip poster for Image-to-Video, or user upload, or text-only
            video_input = uploaded_file or trip_poster_url or None
            video_url = await self.creative_tools.generate_video(
                video_prompt.strip(),
                image_path=video_input
            )
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            video_url = ""

        logger.info(f"Creative Director complete for {destination}: {len(daily_posters)} daily posters, 1 trip poster, video={'yes' if video_url else 'no'}")

        return {
            "agent": self.name,
            "destination": destination,
            "trip_poster_url": trip_poster_url,
            "daily_posters": daily_posters,
            "video_url": video_url,
            "status": "success"
        }
