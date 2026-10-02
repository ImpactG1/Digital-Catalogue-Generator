"""
Digital Catalogue Generator - CLI
Command line interface for generating luxury catalogue pages autonomously.
Supports local physics-based rendering, multi-image Colab Qwen 2.1 inference, and fast relighting.
"""

import os
import sys
import argparse
from typing import List
from catalogue_core import PhotorealisticCompositor, DEFAULT_SLOTS
from colab_bridge import ColabGradioBridge, load_config, save_config


def find_image_files(directory: str) -> List[str]:
    valid_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    files = []
    for f in sorted(os.listdir(directory)):
        if os.path.splitext(f)[1].lower() in valid_exts:
            if "template" not in f.lower() and "output" not in f.lower() and "sample" not in f.lower() and "master" not in f.lower():
                files.append(os.path.join(directory, f))
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Digital Catalogue Generator for Luxury Product Displays."
    )
    parser.add_argument(
        "--template",
        type=str,
        default="Empty Template.png",
        help="Path to the empty template image (default: 'Empty Template.png')"
    )
    parser.add_argument(
        "--products",
        nargs="+",
        help="List of product image files to place onto the template"
    )
    parser.add_argument(
        "--products-dir",
        type=str,
        help="Directory containing product images to process."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="Luxury_Catalogue_Master.png",
        help="Path to save the resulting catalogue image (default: 'Luxury_Catalogue_Master.png')"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save batch generated catalogue pages (default: 'output')"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch process all products into multi-page catalogue (4 products per page)."
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Scaling factor for products inside slots (default: 1.0)"
    )
    parser.add_argument(
        "--y-offset",
        type=int,
        default=0,
        help="Vertical offset adjustment in pixels (default: 0)"
    )
    parser.add_argument(
        "--warmth",
        type=float,
        default=1.0,
        help="Lighting warmth harmonization factor (default: 1.0)"
    )
    parser.add_argument(
        "--gradio-url",
        type=str,
        help="Set or update Google Colab Gradio Live Endpoint URL"
    )
    parser.add_argument(
        "--colab-mode",
        choices=["local", "qwen-multi", "qwen-relight"],
        default="local",
        help="Engine mode: 'local' (fast local physics engine), 'qwen-multi' (Colab Qwen multi-image inpainting), or 'qwen-relight' (Colab AI relighting)"
    )

    args = parser.parse_args()

    bridge = ColabGradioBridge()
    if args.gradio_url:
        print(f"Setting Colab Gradio endpoint to: {args.gradio_url}")
        bridge.set_endpoint(args.gradio_url)

    product_files = []
    if args.products:
        product_files = args.products
    elif args.products_dir:
        if not os.path.exists(args.products_dir):
            print(f"Error: Products directory not found: {args.products_dir}")
            sys.exit(1)
        product_files = find_image_files(args.products_dir)
    else:
        product_files = find_image_files(".")

    if not product_files:
        print("Error: No product images specified or found.")
        sys.exit(1)

    print(f"[Info] Found {len(product_files)} product image(s):")
    for idx, p in enumerate(product_files, 1):
        print(f"  {idx}. {os.path.basename(p)}")

    # Engine Execution
    if args.colab_mode == "qwen-multi" and bridge.is_connected:
        print("[Info] Calling Google Colab Qwen 2.1 Multi-Image Inpainting endpoint...")
        qwen_img = bridge.generate_catalogue_multi(
            template_path=args.template,
            product_paths=product_files[:4]
        )
        if qwen_img:
            qwen_img.save(args.output, quality=95)
            print(f"[Done] Generated catalogue saved to: {args.output}")
            return
        else:
            print("[Warning] Colab multi-image call failed or endpoint not updated. Falling back to local engine...")

    compositor = PhotorealisticCompositor(template_path=args.template)

    if args.batch or len(product_files) > 4:
        print(f"[Info] Running batch generator into directory '{args.output_dir}'...")
        results = compositor.batch_generate(
            product_image_paths=product_files,
            output_dir=args.output_dir,
            scale_factor=args.scale,
            y_offset=args.y_offset,
            warmth=args.warmth
        )
        print(f"[Done] Generated {len(results)} catalogue page(s) in '{args.output_dir}/'")
    else:
        print(f"[Info] Generating catalogue page with marble reflections and contact shadows...")
        page_img = compositor.generate_page(
            product_images=product_files[:4],
            scale_factor=args.scale,
            y_offset=args.y_offset,
            warmth=args.warmth
        )
        page_img.save(args.output, quality=95)
        print(f"[Done] Generated catalogue saved to: {args.output}")

        if args.colab_mode == "qwen-relight" and bridge.is_connected:
            print("[Info] Passing generated layout into Colab for fast AI studio relighting...")
            relit_img = bridge.relight_composite(args.output)
            if relit_img:
                relit_path = args.output.replace(".png", "_relit.png")
                relit_img.save(relit_path, quality=95)
                print(f"[Done] AI relit catalogue saved to: {relit_path}")


if __name__ == "__main__":
    main()
