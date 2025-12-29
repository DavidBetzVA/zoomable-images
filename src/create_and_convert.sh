#!/bin/bash
# Quick script to generate a test image and convert it to DZI

# Use virtual environment if available
if [ -d "env/bin" ]; then
    PYTHON="env/bin/python3"
    echo "Using virtual environment"
else
    PYTHON="python3"
fi

# Default values
WIDTH=${1:-50000}
HEIGHT=${2:-40000}

# Generate timestamp for unique filenames
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_NAME=${3:-"image_${WIDTH}x${HEIGHT}_${TIMESTAMP}"}

# Ensure dzi directory exists
mkdir -p ../output/dzi

echo "======================================"
echo "OPENSEADRAGON IMAGE GENERATOR"
echo "======================================"
echo "Creating ${WIDTH}x${HEIGHT} image..."
echo "Output: ../output/dzi/${OUTPUT_NAME}"
echo ""

# Generate the test image with timestamped name
SOURCE_IMAGE="../output/dzi/${OUTPUT_NAME}.png"
$PYTHON sample_creator.py $WIDTH $HEIGHT "$SOURCE_IMAGE"

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "Converting to DZI tiles..."
    echo ""
    
    # Convert to DZI (output will be in dzi/ directory)
    $PYTHON png_to_dzi.py "$SOURCE_IMAGE" "../output/dzi/${OUTPUT_NAME}"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "======================================"
        echo "✓ ALL DONE!"
        echo "======================================"
        echo "Your OpenSeadragon tiles are ready!"
        echo ""
        echo "Files created:"
        echo "  Source image: ../output/dzi/${OUTPUT_NAME}.png"
        echo "  DZI metadata: ../output/dzi/${OUTPUT_NAME}.dzi"
        echo "  Tiles folder: ../output/dzi/${OUTPUT_NAME}_files/"
        echo ""
        echo "To view in browser:"
        echo "  1. Update index.html tileSources to: 'output/dzi/${OUTPUT_NAME}.dzi'"
        echo "  2. Run: python3 -m http.server 8000"
        echo "  3. Open: http://localhost:8000"
        echo ""
        echo "Or list available DZI files:"
        echo "  ls -lh output/dzi/*.dzi"
        echo ""
    fi
fi
