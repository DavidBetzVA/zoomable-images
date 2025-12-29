#!/usr/bin/env python3
"""
Convert any image format to Deep Zoom Image (DZI) tiles
Supports: PNG, JPG, JPEG, BMP, TIFF, TIF, WEBP, GIF

Usage:
    python3 convert_to_dzi.py input_image.jpg
    python3 convert_to_dzi.py input_image.jpg custom_name
    python3 convert_to_dzi.py input_image.jpg custom_name --tile-size 512 --quality 95
"""

import sys
import os
from pathlib import Path
import argparse
import pyvips

# Supported image formats
SUPPORTED_FORMATS = {
    '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif'
}

def format_bytes(bytes_val):
    """Human-readable file size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

def convert_to_dzi(input_path, output_name=None, tile_size=256, quality=90, overlap=1):
    """
    Convert image to DZI format
    
    Args:
        input_path: Path to input image
        output_name: Optional custom output name (without extension)
        tile_size: Size of each tile (default 256)
        quality: JPEG quality 1-100 (default 90)
        overlap: Pixel overlap between tiles (default 1)
    """
    input_path = Path(input_path)
    
    # Validate input
    if not input_path.exists():
        print(f"❌ Error: File not found: {input_path}")
        return False
    
    if input_path.suffix.lower() not in SUPPORTED_FORMATS:
        print(f"❌ Error: Unsupported format: {input_path.suffix}")
        print(f"   Supported: {', '.join(sorted(SUPPORTED_FORMATS))}")
        return False
    
    # Determine output name
    if output_name:
        base_name = output_name
    else:
        base_name = input_path.stem
    
    # Output paths
    output_dir = Path('../output/dzi')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dzi_path = output_dir / f"{base_name}.dzi"
    tiles_dir = output_dir / f"{base_name}_files"
    
    # Check if output already exists
    if dzi_path.exists():
        response = input(f"⚠️  Output already exists: {dzi_path.name}\n   Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("   Cancelled.")
            return False
    
    print(f"\n{'='*60}")
    print(f"Converting: {input_path.name}")
    print(f"Output: {base_name}.dzi")
    print(f"{'='*60}\n")
    
    # Get input file info
    input_size = input_path.stat().st_size
    print(f"📁 Input file: {format_bytes(input_size)}")
    
    try:
        # Load image
        print(f"📂 Loading image...")
        image = pyvips.Image.new_from_file(str(input_path))
        
        width = image.width
        height = image.height
        megapixels = (width * height) / 1_000_000
        
        print(f"📐 Dimensions: {width:,} × {height:,} pixels")
        print(f"🖼️  Megapixels: {megapixels:.1f} MP")
        print(f"🎨 Channels: {image.bands} ({_get_format_name(image)})")
        print(f"\n🔧 Tile size: {tile_size}×{tile_size}")
        print(f"📊 Quality: {quality}")
        print(f"🔗 Overlap: {overlap}px")
        
        # Calculate expected tiles
        import math
        levels = math.ceil(math.log2(max(width, height))) + 1
        print(f"📚 Zoom levels: {levels}")
        
        # Convert to DZI
        print(f"\n⚙️  Converting to DZI format...")
        image.dzsave(
            str(dzi_path.with_suffix('')),  # pyvips adds .dzi
            tile_size=tile_size,
            overlap=overlap,
            suffix='.jpg[Q={0}]'.format(quality),
            depth='onepixel',
            centre=False,
            layout='dz'
        )
        
        # Count generated tiles
        tile_count = sum(1 for _ in tiles_dir.rglob('*.jpg'))
        
        # Get output size
        dzi_size = dzi_path.stat().st_size
        tiles_size = sum(f.stat().st_size for f in tiles_dir.rglob('*') if f.is_file())
        total_size = dzi_size + tiles_size
        
        print(f"\n✅ Conversion complete!")
        print(f"\n📊 Results:")
        print(f"   DZI file: {format_bytes(dzi_size)}")
        print(f"   Tiles: {tile_count:,} files ({format_bytes(tiles_size)})")
        print(f"   Total: {format_bytes(total_size)}")
        print(f"   Ratio: {total_size/input_size:.1f}x original")
        
        print(f"\n📁 Output location:")
        print(f"   {dzi_path}")
        print(f"   {tiles_dir}/")
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Run: make gallery")
        print(f"   2. Run: make view")
        print(f"   3. Open: http://localhost:8000/")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during conversion: {e}")
        return False

def _get_format_name(image):
    """Get human-readable format name"""
    bands = image.bands
    if bands == 1:
        return "Grayscale"
    elif bands == 2:
        return "Grayscale + Alpha"
    elif bands == 3:
        return "RGB"
    elif bands == 4:
        return "RGBA"
    else:
        return f"{bands} channels"

def main():
    parser = argparse.ArgumentParser(
        description='Convert images to Deep Zoom Image (DZI) format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 convert_to_dzi.py photo.jpg
  python3 convert_to_dzi.py scan.tiff medical_scan
  python3 convert_to_dzi.py image.bmp --tile-size 512 --quality 95
  
Supported formats: PNG, JPG, JPEG, BMP, TIFF, TIF, WEBP, GIF
        """
    )
    
    parser.add_argument('input', help='Input image file path')
    parser.add_argument('output_name', nargs='?', help='Optional output name (default: input filename)')
    parser.add_argument('--tile-size', type=int, default=256, choices=[128, 256, 512],
                       help='Tile size in pixels (default: 256)')
    parser.add_argument('--quality', type=int, default=90,
                       help='JPEG quality 1-100 (default: 90)')
    parser.add_argument('--overlap', type=int, default=1,
                       help='Pixel overlap between tiles (default: 1)')
    
    args = parser.parse_args()
    
    # Validate quality
    if not 1 <= args.quality <= 100:
        print("❌ Error: Quality must be between 1 and 100")
        sys.exit(1)
    
    # Convert
    success = convert_to_dzi(
        args.input,
        args.output_name,
        args.tile_size,
        args.quality,
        args.overlap
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
