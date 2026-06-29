"""
Base Agent
==========

This is the foundational class for all specialized agents in the system.
It handles the integration with Google's Gemini models via the
`google-generativeai` SDK.

It supports:
- Model initialization
- "Thought Signature" (native reasoning capability)
- Standardized error handling
"""

import os
import json
import logging
import asyncio
from google import genai
from google.genai import types
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class BaseAgent:
    """
    Base class for all AI agents.
    
    Attributes:
        name: The name of the agent (e.g., "profiler", "concierge")
        client: The initialized Gemini Client
        model_name: The name of the model to use
    """
    
    def __init__(self, name: str, description: str, model_type: str = "flash"):
        self.name = name
        self.description = description
        
        # Configure the SDK
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
            
        # Select Model based on type
        if model_type == "pro":
            self.model_name = "gemini-3-pro-preview"
        else:
            self.model_name = "gemini-3-flash-preview"
            
        # Default Config + Google Search Grounding
        self.generation_config = {"temperature": 0.7, "max_output_tokens": 8192}

        # Enable Google Search grounding for all agents
        try:
            self.grounding_tool = types.Tool(google_search=types.GoogleSearch())
            logger.info(f"Agent {name} initialized with Google Search grounding enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Search tool: {e}")
            self.grounding_tool = None

    async def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Generates a response from the LLM based on the prompt using the Google Gen AI SDK.
        Includes retry logic for Rate Limits (429).
        """
        if not self.client:
            return "Error: Client not initialized (Missing API Key)"
            
        # Construct final prompt with context if provided
        final_prompt = self._construct_prompt(prompt, context)

        retries = 0
        max_retries = 3
        base_delay = 5  # seconds

        while retries <= max_retries:
            try:
                # Build config with Google Search grounding if available
                config = dict(self.generation_config)
                if self.grounding_tool:
                    config = types.GenerateContentConfig(
                        tools=[self.grounding_tool],
                        temperature=config.get("temperature", 0.7),
                        max_output_tokens=config.get("max_output_tokens", 8192)
                    )

                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model_name,
                    contents=final_prompt,
                    config=config
                )

                return response.text
                
            except Exception as e:
                # Check for Rate Limit / Resource Exhausted
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Agent {self.name} failed after {max_retries} retries due to Rate Limits.")
                        raise
                    
                    wait_time = base_delay * (2 ** (retries - 1)) # 5, 10, 20...
                    logger.warning(f"Rate Limit hit for {self.name}. Retrying in {wait_time}s... (Attempt {retries}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Error generating response for {self.name}: {e}")
                    return "" # Return empty string on non-transient errors to avoid crashing the whole flow
        return ""

    def _construct_prompt(self, base_prompt: str, context: Optional[Dict]) -> str:
        """
        Construct the final prompt by injecting context.
        """
        context_str = ""
        if context:
            context_str = f"\nCONTEXT:\n{context}\n"

        return f"{base_prompt}{context_str}"

    @staticmethod
    def parse_json_response(text: str) -> dict:
        """Strip markdown code fences and parse JSON. Raises json.JSONDecodeError on failure."""
        clean = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
