"""
Digital Catalogue Generator - CLI
Command line interface for generating luxury catalogue pages autonomously.
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
            # Skip templates or outputs
            if "template" not in f.lower() and "output" not in f.lower() and "sample" not in f.lower():
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
        help="List of product image files to place onto the template (e.g. 'Product 1.jpeg' 'Product 2.jpeg' ...)"
    )
    parser.add_argument(
        "--products-dir",
        type=str,
        help="Directory containing product images to process."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="Catalogue_Output.png",
        help="Path to save the resulting catalogue image (default: 'Catalogue_Output.png')"
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

    args = parser.parse_args()

    # Configure Colab endpoint if provided
    bridge = ColabGradioBridge()
    if args.gradio_url:
        print(f"Setting Colab Gradio endpoint to: {args.gradio_url}")
        bridge.set_endpoint(args.gradio_url)

    # Collect product images
    product_files = []
    if args.products:
        product_files = args.products
    elif args.products_dir:
        if not os.path.exists(args.products_dir):
            print(f"Error: Products directory not found: {args.products_dir}")
            sys.exit(1)
        product_files = find_image_files(args.products_dir)
    else:
        # Default auto-discovery in current directory
        product_files = find_image_files(".")

    if not product_files:
        print("Error: No product images specified or found.")
        sys.exit(1)

    print(f"[Info] Found {len(product_files)} product image(s):")
    for idx, p in enumerate(product_files, 1):
        print(f"  {idx}. {os.path.basename(p)}")

    print(f"[Info] Initializing compositor with template: {args.template}...")
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
        print(f"[Info] Generating catalogue page for up to 4 products...")
        page_img = compositor.generate_page(
            product_images=product_files,
            scale_factor=args.scale,
            y_offset=args.y_offset,
            warmth=args.warmth
        )
        page_img.save(args.output, quality=95)
        print(f"[Done] Generated catalogue saved to: {args.output}")


if __name__ == "__main__":
    main()
