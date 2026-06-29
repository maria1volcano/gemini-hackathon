"""
Profiler Agent
==============

This agent uses Gemini 3 to extract user preferences, dietary restrictions,
and travel style from natural language input.
"""

import logging
import json
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from agents.base import BaseAgent

logger = logging.getLogger(__name__)

@dataclass
class TravelerProfile:
    """
    Data class representing a traveler's complete profile.
    """
    dietary_restrictions: list = field(default_factory=list)
    religious_requirements: list = field(default_factory=list)
    allergies: list = field(default_factory=list)
    budget_level: str = "moderate"
    travel_style: str = "balanced"
    accessibility_needs: list = field(default_factory=list)
    group_size: int = 1
    interests: list = field(default_factory=list)
    language_preferences: list = field(default_factory=lambda: ["English"])
    destination: str = ""
    departure_date: str = ""
    return_date: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class ProfilerAgent(BaseAgent):
    """
    Agent responsible for capturing and managing user travel profiles using LLM.
    """

    def __init__(self):
        super().__init__(name="profiler", description="Captures user preferences using LLM", model_type="flash")
        logger.info("ProfilerAgent initialized with LLM")

    GREETINGS = {"hi", "hey", "hello", "hola", "yo", "sup", "what's up", "whats up", "good morning", "good evening"}

    async def async_process(self, query: str, context: Optional[dict] = None) -> dict:
        """
        Process a user query to extract profile information using LLM.
        Profile state is reconstructed from context each call — no shared mutable state.
        """
        context = context or {}

        # Reconstruct profile from incoming context (stateless, safe for concurrent requests)
        current_profile = TravelerProfile()
        for key, value in context.get("profile", {}).items():
            if hasattr(current_profile, key):
                setattr(current_profile, key, value)

        # Extract travel dates from preferences if provided
        preferences = context.get("preferences", {})
        travel_dates = preferences.get("travel_dates", {})
        if travel_dates:
            if travel_dates.get("flexible"):
                # Flexible dates - store the range text for AI to interpret
                current_profile.departure_date = f"FLEXIBLE: {travel_dates.get('range_text', 'anytime')}"
                current_profile.return_date = ""
            else:
                current_profile.departure_date = travel_dates.get("departure", "")
                current_profile.return_date = travel_dates.get("return", "")

        # Short-circuit: greetings need no LLM call
        if query.strip().lower().rstrip("!?.") in self.GREETINGS:
            return {
                "agent": self.name,
                "profile": current_profile.to_dict(),
                "extracted_preferences": [],
                "follow_up_questions": ["Hi there! Where would you like to travel? Tell me about your dream trip!"],
                "status": "greeted"
            }

        prompt = f"""
        Analyze the following user input and extract travel profile information.

        User Input: "{query}"

        Current Profile State:
        {json.dumps(current_profile.to_dict(), indent=2)}

        Task:
        1. Identify any NEW or UPDATED:
           - destination (the city/country the user wants to visit)
           - departure_date (YYYY-MM-DD format if mentioned)
           - return_date (YYYY-MM-DD format if mentioned)
           - dietary_restrictions (e.g., vegetarian, vegan)
           - religious_requirements (e.g., halal, kosher)
           - allergies
           - budget_level (budget, moderate, luxury)
           - travel_style (adventure, relaxation, cultural, etc.)
           - group_size
           - interests
        2. Merge with the Current Profile State.
        3. Highlight what specifically changed.
        4. Generate 1-2 relevant follow-up questions if critical info is missing.

        Output JSON format ONLY:
        {{
            "profile": {{ ...complete profile object... }},
            "changes": ["list of fields changed"],
            "follow_up_questions": ["question 1"]
        }}
        """

        response_text = await self.generate_response(prompt, context=context)

        try:
            data = self.parse_json_response(response_text)

            new_profile_data = data.get("profile", {})
            self._update_profile(current_profile, new_profile_data)

            return {
                "agent": self.name,
                "profile": current_profile.to_dict(),
                "extracted_preferences": data.get("changes", []),
                "follow_up_questions": data.get("follow_up_questions", []),
                "status": "profile_updated"
            }

        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {response_text}")
            return {
                "agent": self.name,
                "profile": current_profile.to_dict(),
                "extracted_preferences": [],
                "follow_up_questions": ["Could you provide more details about your trip?"],
                "status": "error_parsing_llm"
            }

    @staticmethod
    def _update_profile(profile: TravelerProfile, new_data: dict):
        """Merge new data into the profile dataclass."""
        for key, value in new_data.items():
            if hasattr(profile, key):
                current_attr = getattr(profile, key)
                if isinstance(current_attr, list) and isinstance(value, list):
                    merged = list(set(current_attr + value))
                    setattr(profile, key, merged)
                else:
                    setattr(profile, key, value)
