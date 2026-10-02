"""
Google Colab Gradio AI Bridge
Connects to a live Gradio endpoint hosted on Google Colab (e.g., Qwen2.1 Image Pipeline)
Handles both multi-image inputs and text-guided generation.
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
    Client interface for interacting with the Google Colab Gradio endpoint.
    Automatically detects whether the endpoint accepts multi-image inputs or text prompts.
    """

    def __init__(self, endpoint_url: Optional[str] = None):
        cfg = load_config()
        self.endpoint_url = endpoint_url or cfg.get("gradio_endpoint_url", "https://d2963a9a901fe1a4e2.gradio.live").strip()
        self._client = None
        self._is_connected = False
        self._accepts_images = False

    def set_endpoint(self, url: str) -> bool:
        self.endpoint_url = url.strip()
        self._client = None
        self._is_connected = False
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

            # Inspect parameters to determine if endpoint accepts image files
            self._accepts_images = False
            if hasattr(client, "endpoints") and len(client.endpoints) > 0:
                ep = client.endpoints[0]
                for param in ep.parameters:
                    type_str = str(param.get("type", "")).lower()
                    if "filepath" in type_str or "image" in type_str:
                        self._accepts_images = True
                        break

            print(f"[Success] Connected to Colab Gradio: {self.endpoint_url} (Image inputs: {self._accepts_images})")
            return True
        except Exception as e:
            print(f"[Info] Colab Gradio endpoint not reachable: {e}")
            self._is_connected = False
            self._client = None
            return False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def accepts_images(self) -> bool:
        return self._accepts_images

    def generate_with_qwen(
        self,
        prompt: str,
        template_path: str = "Empty Template.png",
        product_paths: Optional[List[str]] = None,
        neg_prompt: str = "blurry, low quality, distorted, extra text",
        steps: int = 30,
        guidance_scale: float = 1.0,
        seed: int = 42,
        api_name: str = "/generate_image_local"
    ) -> Optional[Image.Image]:
        """
        Executes inference on the live Google Colab Gradio endpoint.
        """
        if not self.is_connected and not self.test_connection():
            print("[Warning] Colab endpoint is not connected.")
            return None

        try:
            if self._accepts_images and product_paths:
                # Multi-image endpoint: pass template + 4 products + prompt
                args = [template_path] + product_paths[:4] + [prompt, neg_prompt, steps, guidance_scale, seed]
                result = self._client.predict(*args, api_name=api_name)
            else:
                # Text-prompt endpoint
                result = self._client.predict(
                    prompt=prompt,
                    neg_prompt=neg_prompt,
                    steps=steps,
                    width=1024,
                    height=1024,
                    guidance_scale=guidance_scale,
                    seed=seed,
                    api_name=api_name
                )

            # Parse returned image filepath
            if isinstance(result, tuple) or isinstance(result, list):
                img_path = result[0]
            else:
                img_path = result

            if isinstance(img_path, str) and os.path.exists(img_path):
                return Image.open(img_path).convert("RGB")

            return None
        except Exception as e:
            print(f"[Error] Failed to execute Colab prediction: {e}")
            return None
