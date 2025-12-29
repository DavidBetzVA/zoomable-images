import pyvips
import sys
import os
from pathlib import Path
import time

def convert_to_dzi(input_file, output_name=None, tile_size=256, quality=90, overlap=1):
    """Convert an image to Deep Zoom Image (DZI) format for OpenSeadragon.
    
    Args:
        input_file: Path to input image (PNG, JPEG, TIFF, etc.)
        output_name: Output name without extension (defaults to input filename)
        tile_size: Size of each tile in pixels (default 256, recommended 256 or 512)
        quality: JPEG quality 1-100 (default 90, higher = better quality but larger files)
        overlap: Pixel overlap between tiles (default 1, helps prevent seams)
    
    Returns:
        True if successful, False otherwise
    """
    print("=" * 70)
    print("DZI CONVERTER FOR OPENSEADRAGON")
    print("=" * 70)
    
    # Validate input file
    if not os.path.exists(input_file):
        print(f"✗ Error: Input file '{input_file}' not found")
        return False
    
    # Get file info
    file_size = os.path.getsize(input_file) / 1024 / 1024  # MB
    print(f"\nInput file: {input_file}")
    print(f"File size: {file_size:.1f} MB")
    
    # Set output name
    if output_name is None:
        output_name = Path(input_file).stem
    
    try:
        print(f"\nLoading image...")
        start_time = time.time()
        
        image = pyvips.Image.new_from_file(input_file, access='sequential')
        
        load_time = time.time() - start_time
        print(f"✓ Loaded in {load_time:.1f}s")
        print(f"  Dimensions: {image.width:,} x {image.height:,} pixels")
        print(f"  Channels: {image.bands}")
        print(f"  Format: {image.format}")
        
        # Calculate pyramid levels
        max_dimension = max(image.width, image.height)
        levels = 0
        temp_size = max_dimension
        while temp_size > tile_size:
            temp_size = temp_size / 2
            levels += 1
        levels += 1
        
        # Estimate number of tiles
        total_pixels = 0
        for level in range(levels):
            scale = 2 ** level
            level_width = max(1, image.width // scale)
            level_height = max(1, image.height // scale)
            tiles_x = (level_width + tile_size - 1) // tile_size
            tiles_y = (level_height + tile_size - 1) // tile_size
            total_pixels += tiles_x * tiles_y
        
        print(f"\nConversion settings:")
        print(f"  Tile size: {tile_size}x{tile_size} pixels")
        print(f"  JPEG quality: {quality}")
        print(f"  Tile overlap: {overlap} pixel(s)")
        print(f"  Pyramid levels: {levels}")
        print(f"  Estimated tiles: ~{total_pixels:,}")
        
        print(f"\nConverting to DZI format...")
        print("(This may take several minutes for very large images)")
        
        convert_start = time.time()
        
        # Convert to DZI
        image.dzsave(output_name, 
                     suffix=f'.jpg[Q={quality},optimize_coding=true,strip=true]',
                     tile_size=tile_size,
                     overlap=overlap,
                     depth='onepixel',  # More efficient pyramid
                     centre=False)
        
        convert_time = time.time() - convert_start
        total_time = time.time() - start_time
        
        print(f"\n{'=' * 70}")
        print("✓ CONVERSION COMPLETE!")
        print(f"{'=' * 70}")
        print(f"  Output: {output_name}.dzi")
        print(f"  Tiles directory: {output_name}_files/")
        print(f"  Conversion time: {convert_time:.1f}s")
        print(f"  Total time: {total_time:.1f}s")
        
        # Count actual tiles created
        tiles_dir = f"{output_name}_files"
        if os.path.exists(tiles_dir):
            tile_count = 0
            dir_size = 0
            for root, dirs, files in os.walk(tiles_dir):
                tile_count += len([f for f in files if f.endswith('.jpg')])
                for file in files:
                    dir_size += os.path.getsize(os.path.join(root, file))
            
            print(f"  Total tiles: {tile_count:,}")
            print(f"  Tiles size: {dir_size / 1024 / 1024:.1f} MB")
            print(f"  Avg tile size: {dir_size / tile_count / 1024:.1f} KB")
            print(f"  Compression ratio: {file_size / (dir_size / 1024 / 1024):.1f}x")
        
        print(f"\nNext step: Update your index.html tileSources to '{output_name}.dzi'")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python png_to_dzi.py <input_file> [output_name] [tile_size] [quality]")
        print("\nExample:")
        print("  python png_to_dzi.py huge_test_image.png")
        print("  python png_to_dzi.py my_image.jpg custom_output 512 95")
        print("\nUsing default: huge_test_image.png")
        input_file = 'huge_test_image.png'
        output_name = None
        tile_size = 256
        quality = 90
    else:
        input_file = sys.argv[1]
        output_name = sys.argv[2] if len(sys.argv) > 2 else None
        tile_size = int(sys.argv[3]) if len(sys.argv) > 3 else 256
        quality = int(sys.argv[4]) if len(sys.argv) > 4 else 90
    
    success = convert_to_dzi(input_file, output_name, tile_size, quality)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()