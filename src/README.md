# Image Tile Generator for OpenSeadragon

Simple tools to create test images and convert them to Deep Zoom Image (DZI) format.

## Quick Start

**One command to generate and convert:**

Linux/Mac:
```bash
./create_and_convert.sh
```

Windows (PowerShell):
```powershell
.\create_and_convert.ps1
```

This creates a 50,000 x 40,000 pixel test image and converts it to DZI tiles automatically.

**Custom sizes:**

Linux/Mac:
```bash
./create_and_convert.sh 10000 8000    # Small test (fast)
./create_and_convert.sh 100000 80000  # Large 8 gigapixel image
```

Windows (PowerShell):
```powershell
.\create_and_convert.ps1 -Width 10000 -Height 8000
.\create_and_convert.ps1 -Width 100000 -Height 80000 -OutputName "large_image"
```

## Requirements

```bash
pip install -r requirements.txt

# System library (Ubuntu/Debian):
sudo apt install libvips-dev
```

## Files

- `create_and_convert.sh` - Main script for Linux/Mac
- `create_and_convert.ps1` - Main script for Windows (PowerShell)
- `sample_creator.py` - Creates gradient test images with coordinate grids
- `png_to_dzi.py` - Converts any image to DZI tile format
- `direct_tile_generator.py` - Alternative memory-efficient tile generator
- `requirements.txt` - Python dependencies

## Manual Usage

**Create a test image:**
```bash
python3 sample_creator.py 50000 40000 myimage.png
```

**Convert your own image:**
```bash
python3 png_to_dzi.py photo.jpg output_name
```

## Recommended Sizes

- Small test: 10,000 x 8,000 (~1 minute)
- Medium: 50,000 x 40,000 (~10 minutes)  
- Large: 100,000 x 80,000 (~30 minutes)

## Troubleshooting

**Out of memory?** Reduce image size or use `direct_tile_generator.py`

**Missing fonts?** `sudo apt install fonts-dejavu`

**Slow conversion?** This is normal for large images - pyvips processes millions of tiles
