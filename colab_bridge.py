"""
Google Colab Gradio AI Bridge
Connects to the multi-endpoint Gradio interface hosted on Google Colab (Qwen 2.1).
Supports:
  1. /generate_catalogue_multi (Template + 4 Product Images)
  2. /relight_composite (Fast Studio Relighting & Reflections)
  3. /generate_image_local (Original Text-to-Image)
"""

import os
import json
from typing import Optional, Dict, Any, List
from PIL import Image


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "gradio_endpoint_url": "https://d2963a9a901fe1a4e2.gradio.live",
        "default_template": "Empty Template.png",
        "output_directory": "output",
        "warmth": 1.0,
        "scale_factor": 1.0,
        "y_offset": 0
    }


def save_config(config: Dict[str, Any]):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[Warning] Could not save config: {e}")


class ColabGradioBridge:
    """
    Client interface for interacting with the Google Colab Gradio endpoints.
    Automatically detects available endpoints and provides multi-image inference.
    """

    def __init__(self, endpoint_url: Optional[str] = None):
        cfg = load_config()
        self.endpoint_url = endpoint_url or cfg.get("gradio_endpoint_url", "https://d2963a9a901fe1a4e2.gradio.live").strip()
        self._client = None
        self._is_connected = False
        self._endpoints = []

    def set_endpoint(self, url: str) -> bool:
        self.endpoint_url = url.strip()
        self._client = None
        self._is_connected = False
        self._endpoints = []
        if not self.endpoint_url:
            return False

        cfg = load_config()
        cfg["gradio_endpoint_url"] = self.endpoint_url
        save_config(cfg)

        return self.test_connection()

    def test_connection(self) -> bool:
        if not self.endpoint_url:
            self._is_connected = False
            return False

        try:
            from gradio_client import Client
            client = Client(self.endpoint_url)
            self._client = client
            self._is_connected = True

            # Record available named endpoints
            self._endpoints = []
            if hasattr(client, "endpoints"):
                for ep in client.endpoints:
                    api_name = getattr(ep, "api_name", None)
                    if api_name:
                        self._endpoints.append(api_name if api_name.startswith("/") else f"/{api_name}")

            print(f"[Success] Connected to Colab Gradio: {self.endpoint_url}")
            print(f"[Info] Available endpoints: {self._endpoints}")
            return True
        except Exception as e:
            print(f"[Info] Colab Gradio endpoint not reachable: {e}")
            self._is_connected = False
            self._client = None
            self._endpoints = []
            return False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def available_endpoints(self) -> List[str]:
        return self._endpoints

    def generate_catalogue_multi(
        self,
        template_path: str,
        product_paths: List[str],
        prompt: str = "Place these product images inside template such that they look professionally placed and natural on the marble pedestals. Realistic studio lighting, reflections. Do not name those products or add text.",
        neg_prompt: str = "blurry, distorted, low quality, warped, watermark, extra text, product names",
        steps: int = 30,
        guidance_scale: float = 1.0,
        seed: int = -1
    ) -> Optional[Image.Image]:
        """
        Calls /generate_catalogue_multi on the Colab endpoint with Template + 4 Product Images.
        """
        if not self.is_connected and not self.test_connection():
            return None

        # Pad to 4 products if fewer provided
        p_paths = list(product_paths)
        while len(p_paths) < 4:
            p_paths.append(p_paths[-1] if p_paths else template_path)

        try:
            # Check if multi endpoint exists
            api_name = "/generate_catalogue_multi" if "/generate_catalogue_multi" in self._endpoints else None
            if api_name:
                result = self._client.predict(
                    template_path,
                    p_paths[0],
                    p_paths[1],
                    p_paths[2],
                    p_paths[3],
                    prompt,
                    neg_prompt,
                    steps,
                    guidance_scale,
                    seed,
                    api_name=api_name
                )
                img_path = result[0] if isinstance(result, (tuple, list)) else result
                if isinstance(img_path, str) and os.path.exists(img_path):
                    return Image.open(img_path).convert("RGB")
            else:
                # If endpoint not yet upgraded in Colab, fallback to local engine
                print("[Info] /generate_catalogue_multi not found on Colab. Update Colab cell 14.")
                return None
        except Exception as e:
            print(f"[Error] Colab multi-image prediction failed: {e}")
            return None

    def relight_composite(
        self,
        composite_path: str,
        prompt: str = "High-end luxury studio commercial photography, warm golden reflections on polished marble, photorealistic contact shadows, 8k product render. Keep all ribbons blank.",
        neg_prompt: str = "blurry, distorted, low quality, text on ribbons, logos",
        steps: int = 20,
        guidance_scale: float = 1.0,
        seed: int = -1
    ) -> Optional[Image.Image]:
        """
        Calls /relight_composite on Colab for fast studio relighting & reflections.
        """
        if not self.is_connected and not self.test_connection():
            return None

        try:
            if "/relight_composite" in self._endpoints:
                result = self._client.predict(
                    composite_path,
                    prompt,
                    neg_prompt,
                    steps,
                    guidance_scale,
                    seed,
                    api_name="/relight_composite"
                )
                img_path = result[0] if isinstance(result, (tuple, list)) else result
                if isinstance(img_path, str) and os.path.exists(img_path):
                    return Image.open(img_path).convert("RGB")
            return None
        except Exception as e:
            print(f"[Error] Relight prediction failed: {e}")
            return None
