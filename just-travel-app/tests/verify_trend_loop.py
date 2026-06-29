import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock google.genai BEFORE importing agents
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()
sys.modules["google.genai.types"] = MagicMock()

from agents.trend_spotter import TrendSpotterAgent

async def test_trend_loop():
    print("\n--- Starting Trend Loop Verification ---\n")
    
    agent = TrendSpotterAgent()
    
    # --- Scenario 1: Immediate Success ---
    print("Test 1: Immediate Success")
    # Mock SocialTools to return data immediately
    agent.social_tools.get_trending_hashtags = MagicMock(return_value=["#Paris2024"])
    agent.social_tools.search_travel_content = MagicMock(return_value=[{"title": "Paris Guide", "url": "..."}])
    
    # Mock LLM generation to return valid JSON
    agent.generate_response = AsyncMock(return_value='''
    ```json
    {
        "trends": [{"title": "Cafe de Flore", "trend_score": 90, "description": "Classic", "extracted_locations": ["Paris"]}]
    }
    ```
    ''')
    
    # Pass context with destination
    result = await agent.async_process("Paris", context={"destination": "Paris"})
    print(f"Result Status: {result['status']}")
    print(f"Searched Location: {result['searched_location']}")
    assert result['status'] == "success"
    assert result['searched_location'] == "Paris" # Should not change
    print("✅ Test 1 Passed\n")


    # --- Scenario 2: First Fail, Second Success (Broadening) ---
    print("Test 2: Broadening Loop")
    
    # Reset Agent
    agent = TrendSpotterAgent()
    
    # Mock SocialTools with side_effect
    # Call 1 (Specific): Returns Empty
    # Call 2 (Broad): Returns Data
    agent.social_tools.get_trending_hashtags = MagicMock(side_effect=[[], ["#FranceTravel"]])
    agent.social_tools.search_travel_content = MagicMock(side_effect=[[], [{"title": "France Guide", "url": "..."}]])
    
    # Mock LLM
    # 1. Broadening Query Generation
    # 2. Synthesis for second attempt
    
    async def mock_llm_response(prompt, context=None):
        if "BROADER" in prompt:
            return "France"
        else:
            return '''
            ```json
            {
                "trends": [{"title": "Eiffel Tower", "trend_score": 90, "description": "Classic", "extracted_locations": ["Paris"]}]
            }
            ```
            '''
            
    agent.generate_response = AsyncMock(side_effect=mock_llm_response)

    # Pass context
    result = await agent.async_process("Tiny Village", context={"destination": "Tiny Village"})
    print(f"Result Status: {result['status']}")
    print(f"Searched Location: {result['searched_location']}")
    
    assert result['status'] == "success"
    assert result['searched_location'] == "France" # Should have broadened
    print("✅ Test 2 Passed (Broadened Query)\n")


    # --- Scenario 3: Total Failure ---
    print("Test 3: Total Failure (Max Retries)")
    
    agent = TrendSpotterAgent()
    agent.social_tools.get_trending_hashtags = MagicMock(return_value=[])
    agent.social_tools.search_travel_content = MagicMock(return_value=[])
    
    async def mock_llm_fail(prompt, context=None):
        if "BROADER" in prompt:
             return "BroaderLocation"
        return "{}" # Should fail synthesis if it ever got there, but verify it attempts to broaden
        
    agent.generate_response = AsyncMock(side_effect=mock_llm_fail)
    
    # Pass context
    result = await agent.async_process("Nowhere", context={"destination": "Nowhere"})
    print(f"Result Status: {result['status']}")
    print(f"Raw Count: {result['raw_count']}")
    
    assert result['status'] == "partial_success" or result['status'] == "failed" # Based on code impl
    # Implementation returns "partial_success" if final_trends is empty but code ran without crash
    print("✅ Test 3 Passed (Graceful Exit)\n")

if __name__ == "__main__":
    asyncio.run(test_trend_loop())
