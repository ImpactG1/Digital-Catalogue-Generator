"""
Digital Catalogue Generator - Core Engine
Handles high-precision background extraction, photorealistic contact shadow calculation,
glossy pedestal reflections, lighting harmonization, and template compositing for luxury product catalogues.
"""

import os
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from PIL import Image, ImageOps, ImageFilter
import numpy as np
import cv2


@dataclass
class SlotConfig:
    name: str
    center_x: int
    base_y: int
    max_width: int
    max_height: int
    shadow_opacity: float = 0.85
    ambient_opacity: float = 0.45
    reflection_opacity: float = 0.22


# Calibrated luxury geometry for the 1024x1536 template
DEFAULT_SLOTS = [
    SlotConfig(
        name="Slot 1 (Top Left)",
        center_x=292,
        base_y=765,
        max_width=380,
        max_height=390,
        shadow_opacity=0.85,
        ambient_opacity=0.45,
        reflection_opacity=0.22
    ),
    SlotConfig(
        name="Slot 2 (Top Right)",
        center_x=742,
        base_y=765,
        max_width=380,
        max_height=390,
        shadow_opacity=0.85,
        ambient_opacity=0.45,
        reflection_opacity=0.22
    ),
    SlotConfig(
        name="Slot 3 (Bottom Left)",
        center_x=292,
        base_y=1260,
        max_width=380,
        max_height=390,
        shadow_opacity=0.85,
        ambient_opacity=0.45,
        reflection_opacity=0.22
    ),
    SlotConfig(
        name="Slot 4 (Bottom Right)",
        center_x=742,
        base_y=1260,
        max_width=380,
        max_height=390,
        shadow_opacity=0.85,
        ambient_opacity=0.45,
        reflection_opacity=0.22
    ),
]


class BackgroundRemover:
    """Manages neural background removal with caching and fallback."""

    def __init__(self, model_name: str = "isnet-general-use"):
        self.model_name = model_name
        self.session = None

    def _get_session(self):
        if self.session is None:
            try:
                import rembg
                self.session = rembg.new_session(self.model_name)
            except Exception as e:
                print(f"[Warning] Failed to load {self.model_name}, falling back to u2netp: {e}")
                try:
                    import rembg
                    self.session = rembg.new_session("u2netp")
                except Exception as e2:
                    print(f"[Error] Could not initialize rembg session: {e2}")
                    self.session = None
        return self.session

    def remove_background(self, img: Image.Image, max_dim: int = 1024) -> Image.Image:
        """Removes background and returns an RGBA image cropped to content boundaries."""
        orig_size = img.size
        scale = min(1.0, max_dim / max(orig_size))
        new_size = (int(orig_size[0] * scale), int(orig_size[1] * scale))
        img_resized = img.resize(new_size, Image.Resampling.BILINEAR)

        session = self._get_session()
        if session is not None:
            import rembg
            mask = rembg.remove(img_resized, session=session, only_mask=True)
            mask = mask.resize(orig_size, Image.Resampling.BILINEAR)
            img_rgba = img.convert("RGBA")
            img_rgba.putalpha(mask)
        else:
            img_rgba = img.convert("RGBA")

        # Trim transparent empty borders to find true product bounding box
        bbox = img_rgba.getbbox()
        if bbox:
            img_rgba = img_rgba.crop(bbox)

        return img_rgba


class PhotorealisticCompositor:
    """
    Studio compositor for placing extracted products onto the luxury template.
    Generates multi-layer contact shadows, glossy pedestal floor reflections,
    warm lighting harmonization, and preserves pristine placard gold filigrees.
    """

    def __init__(
        self,
        template_path: str = "Empty Template.png",
        slots: Optional[List[SlotConfig]] = None,
        bg_remover: Optional[BackgroundRemover] = None
    ):
        self.template_path = template_path
        self.slots = slots or DEFAULT_SLOTS
        self.bg_remover = bg_remover or BackgroundRemover()
        self._template = None
        self._placard_overlay = None
        self._load_template()

    def _load_template(self):
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found at: {self.template_path}")
        self._template = Image.open(self.template_path).convert("RGBA")
        self._extract_placards()

    def _extract_placards(self):
        """
        Extracts placard ribbons and golden ornaments from the empty template.
        Preserves the foreground golden emblem and blank ribbon cleanly.
        """
        t_np = np.array(self._template)
        placard_mask = np.zeros(t_np.shape[:2], dtype=bool)

        placard_regions = [
            (775, 875, 70, 510),
            (775, 875, 520, 960),
            (1270, 1370, 70, 510),
            (1270, 1370, 520, 960),
        ]

        for y1, y2, x1, x2 in placard_regions:
            sub = t_np[y1:y2, x1:x2]
            is_ribbon = (sub[:, :, 1] > 20) & (sub[:, :, 0] < 80) & (sub[:, :, 2] < 70)
            is_gold = (sub[:, :, 0] > 160) & (sub[:, :, 1] > 130) & (sub[:, :, 2] < 110)
            placard_mask[y1:y2, x1:x2] = is_ribbon | is_gold

        placards_crop = t_np.copy()
        placards_crop[~placard_mask] = [0, 0, 0, 0]
        self._placard_overlay = Image.fromarray(placards_crop, "RGBA")

    @staticmethod
    def harmonize_lighting(
        prod_rgba: Image.Image,
        warmth: float = 1.0,
        brightness: float = 1.0,
        contrast: float = 1.0
    ) -> Image.Image:
        """
        Blends raw product photography into the template's warm champagne studio lighting.
        """
        rgb = np.array(prod_rgba, dtype=np.float32)
        alpha = rgb[:, :, 3].copy()

        if warmth > 0:
            rgb[:, :, 0] = np.clip(rgb[:, :, 0] * (1.0 + 0.04 * warmth) + 3.0 * warmth, 0, 255)
            rgb[:, :, 1] = np.clip(rgb[:, :, 1] * (1.0 + 0.02 * warmth) + 1.0 * warmth, 0, 255)
            rgb[:, :, 2] = np.clip(rgb[:, :, 2] * (1.0 - 0.04 * warmth), 0, 255)

        if brightness != 1.0:
            rgb[:, :, :3] = np.clip(rgb[:, :, :3] * brightness, 0, 255)

        if contrast != 1.0:
            mean = np.mean(rgb[:, :, :3])
            rgb[:, :, :3] = np.clip((rgb[:, :, :3] - mean) * contrast + mean, 0, 255)

        rgb[:, :, 3] = alpha
        return Image.fromarray(rgb.astype(np.uint8), "RGBA")

    @staticmethod
    def generate_pedestal_reflection(
        prod_rgba: Image.Image,
        max_opacity: float = 0.22,
        blur_radius: float = 3.0
    ) -> Image.Image:
        """
        Simulates subtle reflection on the polished marble pedestal surface.
        """
        flipped = prod_rgba.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        ref_np = np.array(flipped, dtype=np.float32)
        h = ref_np.shape[0]
        grad = np.linspace(max_opacity, 0.0, h).reshape(-1, 1)
        ref_np[:, :, 3] = ref_np[:, :, 3] * grad
        ref_img = Image.fromarray(ref_np.astype(np.uint8), "RGBA")
        if blur_radius > 0:
            ref_img = ref_img.filter(ImageFilter.GaussianBlur(blur_radius))
        return ref_img

    @staticmethod
    def generate_shadows(
        prod_rgba: Image.Image,
        target_w: int,
        target_h: int,
        shadow_opacity: float = 0.85,
        ambient_opacity: float = 0.45
    ) -> Tuple[Image.Image, int, int]:
        """
        Calculates two-tier contact shadow:
        1. Tight contact shadow (ambient occlusion) anchored directly to the bottom footprint.
        2. Diffused ground shadow projected onto the marble podium surface.
        """
        alpha_np = np.array(prod_rgba.split()[-1])
        h, w = alpha_np.shape

        bottom_profile = np.zeros(w, dtype=np.int32)
        has_contact = np.zeros(w, dtype=bool)
        for x in range(w):
            col = np.where(alpha_np[:, x] > 80)[0]
            if len(col) > 0:
                bottom_profile[x] = col.max()
                has_contact[x] = True

        max_prod_y = bottom_profile.max() if has_contact.any() else h - 1

        pad = 40
        sh_w = w + pad * 2
        sh_h = int(h * 0.45) + pad * 2

        # 1. Contact shadow directly at base contact points
        contact_layer = np.zeros((sh_h, sh_w), dtype=np.float32)
        for x in range(w):
            if has_contact[x]:
                y_base = bottom_profile[x]
                sx = x + pad
                sy = (y_base - max_prod_y) + (sh_h // 2)
                for dy in range(-2, 8):
                    if 0 <= sy + dy < sh_h:
                        dist = abs(dy)
                        contact_layer[sy + dy, sx] += max(0.0, 1.0 - dist / 6.0)

        contact_layer = np.clip(contact_layer, 0, 1.0)
        contact_layer = cv2.GaussianBlur(contact_layer, (9, 5), 0)

        # 2. Soft elliptical ambient shadow
        ambient_layer = np.zeros((sh_h, sh_w), dtype=np.float32)
        center_sx = sh_w // 2
        center_sy = sh_h // 2 - 2
        rx = int(w * 0.44)
        ry = max(int(h * 0.08), 10)
        cv2.ellipse(ambient_layer, (center_sx, center_sy), (rx, ry), 0, 0, 360, 1.0, -1)
        ambient_layer = cv2.GaussianBlur(ambient_layer, (25, 13), 0)

        # Combine
        combined_shadow = np.clip(
            ambient_layer * ambient_opacity + contact_layer * shadow_opacity,
            0,
            0.92
        )

        # Warm espresso shadow tone matching the template
        shadow_rgba = np.zeros((sh_h, sh_w, 4), dtype=np.uint8)
        shadow_rgba[:, :, 0] = 30
        shadow_rgba[:, :, 1] = 22
        shadow_rgba[:, :, 2] = 18
        shadow_rgba[:, :, 3] = (combined_shadow * 255).astype(np.uint8)

        shadow_img = Image.fromarray(shadow_rgba, "RGBA")
        return shadow_img, pad, max_prod_y, sh_h

    def place_product(
        self,
        canvas: Image.Image,
        prod_rgba: Image.Image,
        slot: SlotConfig,
        scale_factor: float = 1.0,
        y_offset: int = 0,
        warmth: float = 1.0,
        include_reflection: bool = True
    ):
        """
        Scales, harmonizes, generates shadows & reflections, and composites a single product.
        """
        bbox = prod_rgba.getbbox()
        if bbox:
            prod_rgba = prod_rgba.crop(bbox)

        pw, ph = prod_rgba.size
        if pw == 0 or ph == 0:
            return

        base_scale = min(slot.max_width / pw, slot.max_height / ph)
        final_scale = base_scale * scale_factor

        target_w = max(int(pw * final_scale), 1)
        target_h = max(int(ph * final_scale), 1)

        prod_scaled = prod_rgba.resize((target_w, target_h), Image.Resampling.LANCZOS)
        prod_harmonized = self.harmonize_lighting(prod_scaled, warmth=warmth)

        shadow_img, pad, max_prod_y, sh_h = self.generate_shadows(
            prod_harmonized,
            target_w,
            target_h,
            shadow_opacity=slot.shadow_opacity,
            ambient_opacity=slot.ambient_opacity
        )

        effective_base_y = slot.base_y + y_offset
        pos_x = slot.center_x - target_w // 2
        pos_y = effective_base_y - max_prod_y

        sh_pos_x = pos_x - pad
        sh_pos_y = pos_y + max_prod_y - (sh_h // 2)

        # 1. Composite marble pedestal floor reflection
        if include_reflection and slot.reflection_opacity > 0:
            ref_img = self.generate_pedestal_reflection(
                prod_harmonized,
                max_opacity=slot.reflection_opacity
            )
            canvas.alpha_composite(ref_img, (pos_x, effective_base_y - 4))

        # 2. Composite shadow
        canvas.alpha_composite(shadow_img, (sh_pos_x, sh_pos_y))

        # 3. Composite product
        canvas.alpha_composite(prod_harmonized, (pos_x, pos_y))

    def generate_page(
        self,
        product_images: List[Any],
        scale_factor: float = 1.0,
        y_offset: int = 0,
        warmth: float = 1.0,
        custom_slots: Optional[List[SlotConfig]] = None,
        preserve_placard_overlay: bool = True
    ) -> Image.Image:
        """
        Composites up to 4 products onto a catalogue page.
        """
        slots = custom_slots or self.slots
        canvas = self._template.copy()

        for idx, item in enumerate(product_images):
            if idx >= len(slots):
                break

            slot = slots[idx]

            if isinstance(item, str):
                if not os.path.exists(item):
                    print(f"[Warning] Product image not found: {item}")
                    continue
                raw_img = Image.open(item)
            else:
                raw_img = item

            if raw_img.mode != "RGBA" or np.all(np.array(raw_img.split()[-1]) == 255):
                prod_rgba = self.bg_remover.remove_background(raw_img)
            else:
                prod_rgba = raw_img

            self.place_product(
                canvas=canvas,
                prod_rgba=prod_rgba,
                slot=slot,
                scale_factor=scale_factor,
                y_offset=y_offset,
                warmth=warmth
            )

        if preserve_placard_overlay and self._placard_overlay is not None:
            canvas.alpha_composite(self._placard_overlay, (0, 0))

        return canvas.convert("RGB")

    def batch_generate(
        self,
        product_image_paths: List[str],
        output_dir: str = "output",
        output_prefix: str = "Catalogue_Page",
        **kwargs
    ) -> List[str]:
        """
        Splits a list of N products into 4-product batches and generates catalogue pages.
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []

        chunk_size = len(self.slots)
        chunks = [
            product_image_paths[i:i + chunk_size]
            for i in range(0, len(product_image_paths), chunk_size)
        ]

        for page_num, chunk in enumerate(chunks, 1):
            page_img = self.generate_page(chunk, **kwargs)
            out_filename = f"{output_prefix}_{page_num:02d}.png"
            out_path = os.path.join(output_dir, out_filename)
            page_img.save(out_path, quality=95)
            results.append(out_path)
            print(f"[Success] Generated page {page_num}: {out_path}")

        return results
