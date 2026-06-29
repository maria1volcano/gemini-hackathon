import asyncio
import os
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.creative_tools import CreativeTools
from agents.creative_director import CreativeDirectorAgent

class TestCreativeEngine(unittest.IsolatedAsyncioTestCase):

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "fake_key"})
    @patch("tools.creative_tools.genai.Client")
    async def test_tools_generation(self, mock_client_cls):
        # Setup Mock
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Mock Image Generation
        mock_img_response = MagicMock()
        mock_img_part = MagicMock()
        mock_img_part.inline_data = True
        mock_img_part.as_image.return_value = MagicMock() # Mock PIL image
        mock_img_response.parts = [mock_img_part]
        
        mock_client.models.generate_content = MagicMock(return_value=mock_img_response)
        
        # Mock Video Generation
        mock_video_operation = MagicMock()
        mock_video_operation.done = True
        mock_video_resp = MagicMock()
        mock_video_obj = MagicMock()
        mock_video_obj.video.save = MagicMock()
        mock_video_resp.generated_videos = [mock_video_obj]
        mock_video_operation.response = mock_video_resp
        
        mock_client.models.generate_videos = MagicMock(return_value=mock_video_operation)
        
        # Test Tools
        tools = CreativeTools()
        
        # 1. Test Image
        img_url = await tools.generate_image("test prompt")
        self.assertTrue(img_url.startswith("/generated/gen_img_"))
        print(f"Image Tool verified: {img_url}")

        # 2. Test Video
        vid_url = await tools.generate_video("test prompt")
        self.assertTrue(vid_url.startswith("/generated/gen_video_"))
        print(f"Video Tool verified: {vid_url}")

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "fake_key"})
    @patch("agents.creative_director.CreativeTools")
    @patch("agents.base.genai.Client") # Mock base agent's client too
    async def test_agent_workflow(self, mock_genai, mock_tools_cls):
        # Setup Mocks
        mock_tools = AsyncMock()
        mock_tools.generate_image.return_value = "/generated/poster.png"
        mock_tools.generate_video.return_value = "/generated/video.mp4"
        mock_tools_cls.return_value = mock_tools
        
        # Setup Agent LLM response
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        mock_llm_resp = MagicMock()
        mock_llm_resp.text = '{"poster_prompt": "foo", "video_prompt": "bar"}'
        mock_client.models.generate_content = MagicMock(return_value=mock_llm_resp)

        # Init Agent
        agent = CreativeDirectorAgent()
        
        # Run Process
        plan = {"summary": "Trip to Paris"}
        result = await agent.async_process(plan, context={})
        
        self.assertEqual(result["poster_url"], "/generated/poster.png")
        self.assertEqual(result["video_url"], "/generated/video.mp4")
        print("Creative Director Agent verified")

if __name__ == "__main__":
    unittest.main()
