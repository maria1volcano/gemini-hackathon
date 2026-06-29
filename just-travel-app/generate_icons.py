#!/usr/bin/env python3
"""
Generate PWA icons from SVG source
Creates all required sizes for manifest.json
"""

import cairosvg
from PIL import Image
import io
import os

# Icon sizes required for PWA
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
MASKABLE_SIZES = [192, 512]

INPUT_SVG = "frontend/public/icons/icon.svg"
OUTPUT_DIR = "frontend/public/icons"

def generate_icons():
    """Generate all PNG icons from SVG source"""

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating PWA icons from {INPUT_SVG}...")

    # Generate standard icons
    for size in SIZES:
        output_file = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}.png")

        # Convert SVG to PNG at specified size
        png_data = cairosvg.svg2png(
            url=INPUT_SVG,
            output_width=size,
            output_height=size
        )

        # Save PNG
        with open(output_file, 'wb') as f:
            f.write(png_data)

        print(f"  ✓ Created {output_file}")

    # Generate maskable icons (with padding safe zone)
    for size in MASKABLE_SIZES:
        output_file = os.path.join(OUTPUT_DIR, f"icon-maskable-{size}x{size}.png")

        # Generate at larger size first for padding
        inner_size = int(size * 0.8)  # 80% of final size (20% padding)

        png_data = cairosvg.svg2png(
            url=INPUT_SVG,
            output_width=inner_size,
            output_height=inner_size
        )

        # Load as PIL image
        img = Image.open(io.BytesIO(png_data))

        # Create new image with full size and transparent background
        maskable = Image.new('RGBA', (size, size), (0, 0, 0, 0))

        # Paste centered with padding
        offset = (size - inner_size) // 2
        maskable.paste(img, (offset, offset))

        # Save
        maskable.save(output_file, 'PNG')

        print(f"  ✓ Created {output_file} (maskable)")

    print(f"\n✅ Generated {len(SIZES) + len(MASKABLE_SIZES)} icons successfully!")

if __name__ == "__main__":
    generate_icons()
