"""Enhanced Stability AI integration for image generation."""

import os
import logging
import base64
from typing import Dict, Any, Optional, List, Union
import httpx
import io
from PIL import Image

logger = logging.getLogger(__name__)

class StabilityAIService:
    """Stability AI service for image generation."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Stability AI service.

        Args:
            api_key: Stability AI API key (defaults to STABILITY_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("STABILITY_API_KEY")
        self.api_host = os.getenv("STABILITY_API_HOST", "https://api.stability.ai")

        if not self.api_key:
            logger.warning("STABILITY_API_KEY not set. Stability AI service will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Stability AI service initialized successfully")

    async def generate_image(self,
                            prompt: str,
                            negative_prompt: Optional[str] = None,
                            width: int = 1024,
                            height: int = 1024,
                            cfg_scale: float = 7.0,
                            steps: int = 30,
                            samples: int = 1,
                            engine_id: str = "stable-diffusion-xl-1024-v1-0") -> Dict[str, Any]:
        """Generate an image using Stability AI.

        Args:
            prompt: Prompt to generate the image
            negative_prompt: Optional negative prompt
            width: Width of the image
            height: Height of the image
            cfg_scale: CFG scale
            steps: Number of steps
            samples: Number of samples
            engine_id: Engine ID

        Returns:
            Dictionary containing the generated images
        """
        if not self.enabled:
            return {"error": "Stability AI service is not enabled"}

        try:
            # Prepare the request
            url = f"{self.api_host}/v1/generation/{engine_id}/text-to-image"

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1.0
                    }
                ],
                "cfg_scale": cfg_scale,
                "height": height,
                "width": width,
                "samples": samples,
                "steps": steps
            }

            # Add negative prompt if provided
            if negative_prompt:
                payload["text_prompts"].append({
                    "text": negative_prompt,
                    "weight": -1.0
                })

            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "error": f"Failed to generate image: {error_text}",
                            "status_code": response.status
                        }

                    # Parse the response
                    data = await response.json()

            # Extract the images
            images = []
            for i, image in enumerate(data.get("artifacts", [])):
                image_data = {
                    "base64": image.get("base64"),
                    "seed": image.get("seed"),
                    "finish_reason": image.get("finish_reason")
                }
                images.append(image_data)

            return {
                "images": images,
                "engine_id": engine_id,
                "prompt": prompt,
                "negative_prompt": negative_prompt
            }
        except Exception as e:
            logger.error(f"Failed to generate image with Stability AI: {str(e)}")
            return {"error": str(e)}

    async def generate_email_banner(self,
                                   campaign_data: Dict[str, Any],
                                   width: int = 600,
                                   height: int = 200) -> Dict[str, Any]:
        """Generate an email banner using Stability AI.

        Args:
            campaign_data: Email campaign data
            width: Width of the banner
            height: Height of the banner

        Returns:
            Dictionary containing the generated banner
        """
        if not self.enabled:
            return {"error": "Stability AI service is not enabled"}

        try:
            # Create a prompt based on the campaign data
            campaign_name = campaign_data.get("name", "")
            campaign_subject = campaign_data.get("subject", "")
            campaign_audience = campaign_data.get("audience", "")

            prompt = f"Professional email banner for {campaign_name} campaign. Subject: {campaign_subject}. Target audience: {campaign_audience}. Clean, modern design with brand colors."

            # Generate the image
            result = await self.generate_image(
                prompt=prompt,
                width=width,
                height=height,
                samples=1,
                engine_id="stable-diffusion-xl-1024-v1-0"
            )

            return result
        except Exception as e:
            logger.error(f"Failed to generate email banner with Stability AI: {str(e)}")
            return {"error": str(e)}

    async def generate_product_image(self,
                                    product_description: str,
                                    style: str = "photorealistic",
                                    background: str = "white",
                                    width: int = 1024,
                                    height: int = 1024) -> Dict[str, Any]:
        """Generate a product image using Stability AI.

        Args:
            product_description: Description of the product
            style: Style of the image (e.g., photorealistic, cartoon, 3D render)
            background: Background color or description
            width: Width of the image
            height: Height of the image

        Returns:
            Dictionary containing the generated product image
        """
        if not self.enabled:
            return {"error": "Stability AI service is not enabled"}

        try:
            # Create a prompt based on the product description
            prompt = f"{product_description}, {style} style, {background} background, product photography, high quality, detailed"

            # Add negative prompt for better quality
            negative_prompt = "low quality, blurry, distorted, deformed, disfigured, text, watermark"

            # Generate the image
            result = await self.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                samples=1,
                cfg_scale=8.0,
                steps=40,
                engine_id="stable-diffusion-xl-1024-v1-0"
            )

            return result
        except Exception as e:
            logger.error(f"Failed to generate product image with Stability AI: {str(e)}")
            return {"error": str(e)}

    async def generate_social_media_image(self,
                                        content: str,
                                        platform: str = "instagram",
                                        style: str = "modern",
                                        width: int = 1080,
                                        height: int = 1080) -> Dict[str, Any]:
        """Generate a social media image using Stability AI.

        Args:
            content: Content description for the image
            platform: Social media platform (e.g., instagram, twitter, facebook)
            style: Style of the image
            width: Width of the image
            height: Height of the image

        Returns:
            Dictionary containing the generated social media image
        """
        if not self.enabled:
            return {"error": "Stability AI service is not enabled"}

        try:
            # Adjust dimensions based on platform
            if platform.lower() == "instagram":
                width, height = 1080, 1080  # Square format
            elif platform.lower() == "twitter":
                width, height = 1200, 675  # 16:9 format
            elif platform.lower() == "facebook":
                width, height = 1200, 630  # Recommended for link shares
            elif platform.lower() == "linkedin":
                width, height = 1200, 627  # Recommended for link shares

            # Create a prompt based on the content and platform
            prompt = f"{content}, {style} style, optimized for {platform}, social media post, high quality, engaging, eye-catching"

            # Add negative prompt for better quality
            negative_prompt = "low quality, blurry, distorted, deformed, disfigured, text, watermark"

            # Generate the image
            result = await self.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                samples=1,
                cfg_scale=7.5,
                steps=35,
                engine_id="stable-diffusion-xl-1024-v1-0"
            )

            return result
        except Exception as e:
            logger.error(f"Failed to generate social media image with Stability AI: {str(e)}")
            return {"error": str(e)}

    async def resize_image(self,
                          base64_image: str,
                          width: int,
                          height: int) -> Optional[str]:
        """Resize an image.

        Args:
            base64_image: Base64-encoded image
            width: Target width
            height: Target height

        Returns:
            Base64-encoded resized image if successful, None otherwise
        """
        try:
            # Decode the base64 image
            image_data = base64.b64decode(base64_image)

            # Open the image
            with Image.open(io.BytesIO(image_data)) as img:
                # Resize the image
                resized_img = img.resize((width, height), Image.LANCZOS)

                # Save the resized image to a buffer
                buffer = io.BytesIO()
                resized_img.save(buffer, format=img.format or "PNG")

                # Encode the resized image as base64
                resized_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

                return resized_base64
        except Exception as e:
            logger.error(f"Failed to resize image: {str(e)}")
            return None

    async def generate_image_variations(self,
                                       base64_image: str,
                                       num_variations: int = 3,
                                       strength: float = 0.7,
                                       engine_id: str = "stable-diffusion-xl-1024-v1-0") -> Dict[str, Any]:
        """Generate variations of an image using Stability AI.

        Args:
            base64_image: Base64-encoded image
            num_variations: Number of variations to generate
            strength: Strength of the variations (0.0 to 1.0)
            engine_id: Engine ID

        Returns:
            Dictionary containing the generated image variations
        """
        if not self.enabled:
            return {"error": "Stability AI service is not enabled"}

        try:
            # Prepare the request
            url = f"{self.api_host}/v1/generation/{engine_id}/image-to-image"

            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            # Decode the base64 image
            image_data = base64.b64decode(base64_image)

            # Prepare the form data
            form_data = aiohttp.FormData()
            form_data.add_field("init_image", image_data, filename="init_image.png", content_type="image/png")
            form_data.add_field("text_prompts[0][text]", "Enhance this image, make it more professional and polished")
            form_data.add_field("text_prompts[0][weight]", "1.0")
            form_data.add_field("cfg_scale", str(7.0))
            form_data.add_field("samples", str(num_variations))
            form_data.add_field("steps", str(30))
            form_data.add_field("image_strength", str(strength))

            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=form_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "error": f"Failed to generate image variations: {error_text}",
                            "status_code": response.status
                        }

                    # Parse the response
                    data = await response.json()

            # Extract the images
            images = []
            for i, image in enumerate(data.get("artifacts", [])):
                image_data = {
                    "base64": image.get("base64"),
                    "seed": image.get("seed"),
                    "finish_reason": image.get("finish_reason")
                }
                images.append(image_data)

            return {
                "images": images,
                "engine_id": engine_id,
                "strength": strength
            }
        except Exception as e:
            logger.error(f"Failed to generate image variations with Stability AI: {str(e)}")
            return {"error": str(e)}

# Create a singleton instance
stability_ai_service = StabilityAIService()
