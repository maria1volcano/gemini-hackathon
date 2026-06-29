import os
import logging
import asyncio
import time
import base64
from io import BytesIO
from typing import Optional
from google import genai
from google.genai import types

# Configure logging
logger = logging.getLogger(__name__)

class CreativeTools:
    """
    Tools for generating visual assets using Gemini 3 Pro (Vision) and Veo 3.1.
    """

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found. Creative tools will not work.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            
        self.image_model = "gemini-3-pro-image-preview"  # Nano Banana Pro
        self.video_model = "veo-3.1-generate-preview"    # Veo 3.1
        
        # Base paths for saving assets
        # Defined relative to the python backend execution, but they need to land in frontend/public
        self.output_dir_base = os.path.join(os.getcwd(), "frontend", "public")
        self.generated_dir = os.path.join(self.output_dir_base, "generated")
        self.uploads_dir = os.path.join(self.output_dir_base, "uploads")
        
        # Ensure directories exist
        os.makedirs(self.generated_dir, exist_ok=True)
        os.makedirs(self.uploads_dir, exist_ok=True)

    async def generate_image(self, prompt: str, aspect_ratio: str = "16:9") -> str:
        """
        Generates an image using Gemini 3 Pro Image.
        Returns the relative URL path for the frontend.
        """
        if not self.client:
            return ""

        logger.info(f"Generating image for prompt: {prompt[:50]}...")
        
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.image_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE'],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size="2K" 
                    )
                )
            )
            
            # Extract and save image
            for part in response.parts:
                if part.inline_data:
                    timestamp = int(time.time())
                    filename = f"gen_img_{timestamp}.png"
                    filepath = os.path.join(self.generated_dir, filename)
                    
                    # Save using the SDK's helper if available, or manual save
                    # The SDK part object usually has an `as_image()` helper if PIL is installed,
                    # but `inline_data.data` contains the bytes.
                    
                    image_obj = part.as_image()
                    await asyncio.to_thread(image_obj.save, filepath)
                    
                    logger.info(f"Image saved to {filepath}")
                    return f"/generated/{filename}"
                    
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return ""
            
        return ""

    async def generate_video(self, prompt: str, image_path: Optional[str] = None) -> str:
        """
        Generates a video using Veo 3.1.
        Can be text-to-video or image-to-video if image_path is provided.
        Returns the relative URL path for the frontend.
        """
        if not self.client:
            return ""

        logger.info(f"Generating video for prompt: {prompt[:50]}... (Image input: {image_path})")
        
        try:
            # 1. Prepare image input if provided
            pil_image = None
            if image_path:
                if image_path.startswith("/"):
                    abs_image_path = os.path.join(self.output_dir_base, image_path.lstrip("/"))
                else:
                    abs_image_path = image_path

                if os.path.exists(abs_image_path):
                    from PIL import Image
                    pil_image = Image.open(abs_image_path)
                else:
                    logger.warning(f"Image path not found: {abs_image_path}. Falling back to text-to-video.")

            # 2. Call API (Long Running Operation)
            operation = None
            if pil_image:
                try:
                    # Convert PIL image to bytes, then create types.Image
                    img_buffer = BytesIO()
                    pil_image.save(img_buffer, format='PNG')
                    img_bytes = img_buffer.getvalue()

                    # Create proper SDK Image object with image_bytes
                    image_obj = types.Image(image_bytes=img_bytes, mime_type='image/png')

                    operation = await asyncio.to_thread(
                        self.client.models.generate_videos,
                        model=self.video_model,
                        prompt=prompt,
                        image=image_obj
                    )
                except Exception as img_error:
                    # If image-to-video fails, fall back to text-to-video
                    logger.warning(f"Image-to-video failed: {img_error}. Using text-to-video instead.")
                    operation = await asyncio.to_thread(
                        self.client.models.generate_videos,
                        model=self.video_model,
                        prompt=prompt
                    )
            else:
                operation = await asyncio.to_thread(
                    self.client.models.generate_videos,
                    model=self.video_model,
                    prompt=prompt
                )

            # 3. Poll for completion (with timeout)
            max_poll_seconds = 300  # 5-minute cap
            poll_start = time.time()
            while not operation.done:
                if time.time() - poll_start > max_poll_seconds:
                    logger.error("Video generation timed out after 5 minutes.")
                    return ""
                logger.info("Waiting for video generation...")
                await asyncio.sleep(10)
                operation = await asyncio.to_thread(
                    self.client.operations.get,
                    operation
                )

            # 4. Save Video
            if operation.response and operation.response.generated_videos:
                video_obj = operation.response.generated_videos[0]

                timestamp = int(time.time())
                filename = f"gen_video_{timestamp}.mp4"
                filepath = os.path.join(self.generated_dir, filename)

                # Handle both remote URI and local bytes
                video_saved = False
                if hasattr(video_obj.video, 'uri') and video_obj.video.uri:
                    # Download from remote URI
                    import httpx
                    logger.info(f"Downloading video from remote URI: {video_obj.video.uri[:50]}...")
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.get(video_obj.video.uri)
                        response.raise_for_status()
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        video_saved = True
                elif hasattr(video_obj.video, 'video_bytes') and video_obj.video.video_bytes:
                    # Save local bytes directly
                    with open(filepath, 'wb') as f:
                        f.write(video_obj.video.video_bytes)
                    video_saved = True
                else:
                    # Fallback: try the SDK save method
                    try:
                        await asyncio.to_thread(video_obj.video.save, filepath)
                        video_saved = True
                    except Exception as save_err:
                        logger.error(f"SDK save failed: {save_err}")

                if video_saved:
                    logger.info(f"Video saved to {filepath}")
                    return f"/generated/{filename}"
                else:
                    logger.error("Could not save video - no valid source found")
                    return ""
            else:
                logger.error("Video generation completed but returned no videos.")
                return ""

        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return ""

