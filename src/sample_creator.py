from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import sys
from datetime import datetime
import math

def create_test_image(width=50000, height=40000, grid_spacing=2000, label_spacing=4000):
    """Create a visually complex test image demonstrating deep zoom quality.
    
    Features multiple visual elements at different scales:
    - Gradient background
    - Fine grid pattern (shows detail at medium zoom)
    - Sine wave patterns (demonstrates curve rendering)
    - Radial patterns (circles, spirals)
    - Text labels at multiple scales
    - Texture patterns (checkerboards, dots)
    
    Args:
        width: Image width in pixels (default 50000)
        height: Image height in pixels (default 40000)
        grid_spacing: Spacing between major grid lines in pixels (default 2000)
        label_spacing: Spacing between coordinate labels in pixels (default 4000)
    """
    print(f"Creating {width:,} x {height:,} pixel image...")
    print(f"Estimated size: {(width * height * 3 / 1024 / 1024):.1f} MB in memory")
    
    # Create multi-colored gradient background using numpy (memory-efficient approach)
    print("Generating gradient background...")
    
    # Create image array directly (more memory efficient than separate channels)
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    print("  - Creating vertical gradient (R channel)...")
    img_array[:, :, 0] = np.linspace(0, 255, height, dtype=np.uint8).reshape(-1, 1)
    
    print("  - Creating horizontal gradient (G channel)...")
    img_array[:, :, 1] = np.linspace(0, 255, width, dtype=np.uint8).reshape(1, -1)
    
    print("  - Creating radial gradient (B channel)...")
    center_x, center_y = width // 2, height // 2
    # Process in chunks to avoid memory issues with huge arrays
    chunk_size = 1000
    for y_start in range(0, height, chunk_size):
        y_end = min(y_start + chunk_size, height)
        for x_start in range(0, width, chunk_size):
            x_end = min(x_start + chunk_size, width)
            
            y_coords = np.arange(y_start, y_end).reshape(-1, 1) - center_y
            x_coords = np.arange(x_start, x_end).reshape(1, -1) - center_x
            
            distances = np.sqrt(y_coords**2 + x_coords**2)
            max_dist = np.sqrt(center_x**2 + center_y**2)
            img_array[y_start:y_end, x_start:x_end, 2] = (255 - (distances / max_dist * 255)).astype(np.uint8)
    
    print("  - Converting to PIL Image...")
    img = Image.fromarray(img_array, 'RGB')
    
    # Free the numpy array memory
    del img_array
    
    draw = ImageDraw.Draw(img)
    
    # Draw fine grid (shows detail when zooming)
    print("Drawing fine grid pattern...")
    fine_spacing = grid_spacing // 4
    grid_count = 0
    for x in range(0, width, fine_spacing):
        is_major = (x % grid_spacing == 0)
        color = 'white' if is_major else (200, 200, 200)
        line_width = 4 if is_major else 1
        draw.line([(x, 0), (x, height)], fill=color, width=line_width)
        grid_count += 1
    
    for y in range(0, height, fine_spacing):
        is_major = (y % grid_spacing == 0)
        color = 'white' if is_major else (200, 200, 200)
        line_width = 4 if is_major else 1
        draw.line([(0, y), (width, y)], fill=color, width=line_width)
        grid_count += 1
    
    print(f"Drew {grid_count} grid lines (fine + major)")
    
    # Draw sine wave patterns (demonstrates curves at different scales)
    print("Drawing sine wave patterns...")
    wave_count = 0
    num_waves = 5
    for i in range(num_waves):
        amplitude = height // (2 * num_waves) * (i + 1) / num_waves
        frequency = (i + 1) * 0.001
        y_offset = height // 2
        
        points = []
        for x in range(0, width, 10):  # Sample every 10 pixels
            y = int(y_offset + amplitude * math.sin(frequency * x))
            points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill=(255, 255, 0), width=3)
            wave_count += 1
    
    print(f"Drew {wave_count} sine waves")
    
    # Draw concentric circles (radial patterns for zoom detail)
    print("Drawing concentric circles...")
    center_x, center_y = width // 2, height // 2
    max_radius = min(width, height) // 2
    circle_count = 0
    for radius in range(100, max_radius, 200):
        bbox = [center_x - radius, center_y - radius, 
                center_x + radius, center_y + radius]
        draw.ellipse(bbox, outline=(0, 255, 255), width=2)
        circle_count += 1
    
    print(f"Drew {circle_count} concentric circles")
    
    # Draw spiral pattern
    print("Drawing spiral pattern...")
    spiral_points = []
    max_angle = 20 * math.pi  # 10 full rotations
    steps = 2000
    for i in range(steps):
        angle = (i / steps) * max_angle
        radius = (i / steps) * (max_radius * 0.8)
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        spiral_points.append((x, y))
    
    if len(spiral_points) > 1:
        draw.line(spiral_points, fill=(255, 0, 255), width=3)
        print("Drew spiral")
    
    # Draw checkerboard pattern in corners (fine detail test)
    print("Drawing checkerboard patterns in corners...")
    checker_size = 20
    checker_area = 500
    
    # Top-left corner
    for x in range(0, checker_area, checker_size):
        for y in range(0, checker_area, checker_size):
            if (x // checker_size + y // checker_size) % 2 == 0:
                draw.rectangle([x, y, x + checker_size, y + checker_size], 
                             fill=(255, 255, 255))
    
    # Top-right corner
    for x in range(width - checker_area, width, checker_size):
        for y in range(0, checker_area, checker_size):
            if ((x - (width - checker_area)) // checker_size + y // checker_size) % 2 == 0:
                draw.rectangle([x, y, x + checker_size, y + checker_size], 
                             fill=(255, 255, 255))
    
    # Bottom-left corner
    for x in range(0, checker_area, checker_size):
        for y in range(height - checker_area, height, checker_size):
            if (x // checker_size + (y - (height - checker_area)) // checker_size) % 2 == 0:
                draw.rectangle([x, y, x + checker_size, y + checker_size], 
                             fill=(255, 255, 255))
    
    # Bottom-right corner
    for x in range(width - checker_area, width, checker_size):
        for y in range(height - checker_area, height, checker_size):
            if ((x - (width - checker_area)) // checker_size + 
                (y - (height - checker_area)) // checker_size) % 2 == 0:
                draw.rectangle([x, y, x + checker_size, y + checker_size], 
                             fill=(255, 255, 255))
    
    print("Drew checkerboard patterns in 4 corners")
    
    # Draw dot pattern (shows anti-aliasing and detail preservation)
    print("Drawing dot pattern...")
    dot_count = 0
    dot_spacing = 100
    dot_radius = 8
    for x in range(dot_spacing, min(width, 2000), dot_spacing):
        for y in range(dot_spacing, min(height, 2000), dot_spacing):
            draw.ellipse([x - dot_radius, y - dot_radius, 
                         x + dot_radius, y + dot_radius], 
                        fill=(255, 128, 0))
            dot_count += 1
    
    print(f"Drew {dot_count} dots")
    
    # Load font (try multiple common locations)
    font = None
    font_paths = [
        "fonts/TimesNewRoman.ttf"
    ]
    
    # Scale font size based on image dimensions
    font_size = max(50, min(width, height) // 100)
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                print(f"Using font: {os.path.basename(font_path)} (size {font_size})")
                break
            except Exception as e:
                continue
    
    if not font:
        print("Warning: Using default font (may be small)")
        font = ImageFont.load_default()
    
    # Add coordinate labels
    label_count = 0
    for x in range(0, width, label_spacing):
        for y in range(0, height, label_spacing):
            label = f"{x:,},{y:,}"
            # Add black outline for better visibility
            offset = 3
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx != 0 or dy != 0:
                        draw.text((x+100+dx, y+100+dy), label, fill='black', font=font)
            draw.text((x+100, y+100), label, fill='yellow', font=font)
            label_count += 1
    
    print(f"Added {label_count} coordinate labels")
    
    return img

def main():
    # Create output/dzi directory if it doesn't exist
    os.makedirs('../output/dzi', exist_ok=True)
    
    # Parse command line arguments
    width = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    height = int(sys.argv[2]) if len(sys.argv) > 2 else 40000
    
    # Generate timestamped filename if not provided
    if len(sys.argv) > 3:
        output_file = sys.argv[3]
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'../output/dzi/image_{width}x{height}_{timestamp}.png'
    
    print("=" * 60)
    print("MASSIVE IMAGE GENERATOR FOR OPENSEADRAGON")
    print("=" * 60)
    
    # Generate image
    img = create_test_image(width, height)
    
    # Save with progress
    print(f"\nSaving to '{output_file}'...")
    print("(This may take a while for large images)")
    
    try:
        img.save(output_file, 'PNG', optimize=False)
        
        # Get file size
        file_size = os.path.getsize(output_file)
        print(f"\n✓ SUCCESS!")
        print(f"  File: {output_file}")
        print(f"  Size: {file_size / 1024 / 1024:.1f} MB")
        print(f"  Dimensions: {width:,} x {height:,} pixels")
        print(f"\nNext step: Run 'python png_to_dzi.py {output_file}' to generate tiles")
        
    except Exception as e:
        print(f"\n✗ Error saving image: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()