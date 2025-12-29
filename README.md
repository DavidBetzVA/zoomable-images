# OpenSeadragon Deep Zoom Image Viewer

A VA-compliant, Section 508 accessible gallery and viewer for massive high-resolution images using OpenSeadragon's deep zoom technology. Convert any image format (PNG, JPG, BMP, TIFF, WEBP, GIF, DICOM) or generate test images with full accessibility support.

See demo at [http://seadragon-demo-cwbefuwek.s3-website-us-east-1.amazonaws.com](http://seadragon-demo-cwbefuwek.s3-website-us-east-1.amazonaws.com)

## Simple Usage

### Convert Your Images

```bash
# Any image format (PNG, JPG, BMP, TIFF, WEBP, GIF)
# Samples from https://svs.gsfc.nasa.gov/vis/a030000/a030800/a030877/frames/5760x3240_16x9_01p/
make convert INPUT=./samples/BlackMarble_2016_928m_europe_labeled.png
make convert INPUT=./samples/BlackMarble_2016_928m_mediterranean.tif

# Medical images (DICOM)
# Samples from https://www.rubomedical.com/dicom_files/
make convert-dicom INPUT=./samples/0015.dcm
make convert-dicom INPUT=./samples/mrbrain.dcm

# Medical images (DICOM) - Multi-frame
make convert-dicom INPUT=./samples/0002-multiframe.dcm FRAMES=all

# View in browser
make view
# Open: http://localhost:8000/
```

### Supported Image Formats

**PNG** - Lossless, transparency  
**JPEG/JPG** - Photos, scans  
**BMP** - Windows bitmaps  
**TIFF** - Medical/scientific imaging  
**WEBP** - Modern web format  
**GIF** - Animated (first frame)  
**DICOM** - Medical imaging (.dcm files, single/multi-frame)  

---

## Advanced Usage

### Custom Image Conversion

```bash
# Custom output name
make convert INPUT=scan.tiff OUTPUT_NAME=medical_scan

# High quality for diagnostic review
make convert INPUT=pathology.jpg QUALITY=95 TILE_SIZE=512

# Batch convert all JPG files
for img in *.jpg; do
    make convert INPUT="$img"
done
```

### DICOM Medical Imaging

```bash
# Basic DICOM conversion
make convert-dicom INPUT=ct_slice.dcm

# Custom name and high quality
make convert-dicom INPUT=pathology.dcm OUTPUT_NAME=patient_001 QUALITY=95

# Multi-frame DICOM (angiograms, cine loops)
make convert-dicom INPUT=angiogram.dcm FRAMES=all        # Convert all frames
make convert-dicom INPUT=cine.dcm FRAMES=50              # Convert frame 50 only

# Batch convert DICOM studies
for dcm in study_*.dcm; do
    make convert-dicom INPUT="$dcm"
done
```

**DICOM Features:**
- Automatic windowing and level adjustments
- Hounsfield unit rescaling (CT scans)
- MONOCHROME1/2 inversion handling
- Metadata extraction (modality, patient ID, study date)
- Multi-frame support with video-like playback viewer

### Development & Testing

Generate synthetic test images for development and testing:

```bash
# Quick demo (start here)
make demo           # Generate tiny image + view

# Preset test images
make tiny           # 2000 x 2000 (visual testing)
make quick          # 5000 x 4000 (quick demo)
make medium         # 50000 x 40000 (2 gigapixels)
make large          # 100000 x 80000 (8 gigapixels)
make extreme        # 200000 x 160000 (32 gigapixels)

# Custom dimensions
make generate WIDTH=60000 HEIGHT=48000 OUTPUT_NAME=my_test_image
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `INPUT` | Required | Path to image file |
| `OUTPUT_NAME` | filename | Custom output name |
| `TILE_SIZE` | 256 | Tile size: 128, 256, or 512 |
| `QUALITY` | 90 | JPEG quality: 1-100 |
| `WIDTH` | 50000 | Image width (generation) |
| `HEIGHT` | 40000 | Image height (generation) |
| `PORT` | 8000 | HTTP server port |

### Direct Script Usage

```bash
# Convert via shell script
cd src
./convert.sh path/to/image.jpg custom_name

# Convert via Python
python3 convert_to_dzi.py image.jpg output_name --tile-size 512 --quality 95

# Convert DICOM via Python
python3 convert_dicom_to_dzi.py scan.dcm patient_001 --tile-size 512

# Generate test image manually
./create_and_convert.sh 50000 40000 my_test_image
```

---

## Project Structure

```
large-image-viewer-demo/
├── Makefile                    # Build automation
├── README.md                   # This file
├── viewer.html                 # Viewer template
├── output/                     # Generated gallery and DZI files
│   ├── index.html             # Gallery (508 compliant)
│   ├── viewer.html            # Viewer (508 compliant)
│   └── dzi/                   # Deep Zoom Image tiles
│       ├── *.dzi              # Image metadata
│       └── *_files/           # Tile pyramids (0/ to N/)
└── src/                       # Image processing tools
    ├── convert_to_dzi.py      # Image converter
    ├── convert_dicom_to_dzi.py # DICOM converter
    ├── generate_index.py      # Gallery generator
    ├── sample_creator.py      # Test image generator
    ├── png_to_dzi.py          # DZI tile generator
    ├── requirements.txt       # Python dependencies
    └── env/                   # Python virtual environment
```

## Features

- **VA/USWDS Compliant** - Official VA design colors (#162e51)
- **Section 508 Accessible** - ARIA labels, semantic HTML, keyboard navigation
- **Auto-Generated** - Scans DZI files automatically
- **Responsive** - Desktop, tablet, mobile
- **Image Stats** - Dimensions, file sizes, tile counts

- **Deep Zoom** - Smooth zoom for massive images
- **Keyboard Support** - 0/Home (reset), +/- (zoom), F (fullscreen), R (rotate), arrows (pan)
- **Touch Support** - Pinch/drag gestures
- **Rotation & Flip** - 90° rotation, horizontal mirror
- **Fullscreen** - Immersive viewing
- **ARIA Live Regions** - Screen reader announcements

### Accessibility (Section 508 / WCAG 2.1 AA)
- Semantic HTML5 landmarks
- Skip links for keyboard users
- Full keyboard navigation
- ARIA labels and live regions
- Focus indicators (2px blue outlines)
- VA color scheme with proper contrast ratios

---

## Installation

### System Requirements
- Python 3.7+
- libvips (image processing library)
- Make (build automation)

### Python Dependencies
```
pillow>=10.0.0    # Image processing
numpy>=1.24.0     # Numerical arrays
pyvips>=2.2.0     # Tile generation
pydicom>=2.4.0    # DICOM medical imaging
```

---

## Technical Details

### Deep Zoom Image (DZI) Format
- Multi-resolution image pyramid (level 0 to N)
- Each level is 50% smaller than the previous
- Images divided into tiles (typically 256×256 pixels)
- Only loads visible tiles = efficient for massive images
- JPEG-compressed tiles with configurable quality

### Why OpenSeadragon
- Pure JavaScript, no plugins required
- Handles images of ANY size (tested up to 200K×160K)
- Smooth, hardware-accelerated rendering
- Mobile and touch support built-in
- Extensive API for customization
- CDN-hosted, zero local dependencies

### Performance
- **Tile Loading** - Only loads visible tiles + 1-tile buffer
- **Memory Usage** - ~50-200 MB regardless of image size
- **Network** - Progressive loading, instant viewing
- **Rendering** - Hardware-accelerated Canvas/WebGL
- **Generation** - pyvips processes in chunks (memory efficient)

### Image Size Guide

| Preset | Dimensions | Megapixels | Tiles | Gen Time | Use Case |
|--------|-----------|-----------|-------|----------|----------|
| **tiny** | 2K × 2K | 4 MP | ~93 | <1 min | Visual testing |
| **quick** | 5K × 4K | 20 MP | ~150 | ~1 min | Quick demo |
| **medium** | 50K × 40K | 2 GP | ~5000 | ~10 min | Standard demo |
| **large** | 100K × 80K | 8 GP | ~20000 | ~30 min | Impressive demo |
| **extreme** | 200K × 160K | 32 GP | ~80000 | ~2 hrs | Stress test |

---

## Troubleshooting

### Python Not Found
```bash
# Recreate virtual environment
rm -rf src/env
python3 -m venv src/env
source src/env/bin/activate
pip install -r src/requirements.txt
```

### File Not Found During Conversion
- Use absolute paths or paths relative to project root
- Example: `make convert INPUT=./image.jpg` (not `INPUT=../image.jpg`)

### Server Won't Start
```bash
# Port already in use - try different port
make view PORT=8080

# Stop existing server
make stop-server
```

### Images Not Appearing in Gallery
```bash
# Regenerate gallery
make gallery

# Verify DZI files exist
ls output/dzi/*.dzi
```

### Image Not Loading in Viewer
- Open browser console (F12) for errors
- Verify files exist: `output/dzi/imagename.dzi` and `output/dzi/imagename_files/`
- Check HTTP server is running
- Check network tab for failed tile requests

### Out of Memory During Generation
- Reduce image dimensions
- Close other applications
- Monitor with `htop` or Task Manager
- Normal memory usage: tiny=200MB, medium=1GB, large=2-4GB, extreme=8GB+

### Slow Generation
- Normal for large images - pyvips processes in chunks
- Time estimates: tiny=30s, medium=10min, large=30min, extreme=2hr
- Use lower quality/larger tiles to speed up: `TILE_SIZE=512 QUALITY=85`

### Accessibility Testing
- Validate with axe DevTools or WAVE browser extension
- Test keyboard navigation (Tab, arrows, shortcuts)
- Test with screen reader (NVDA, JAWS, VoiceOver)
- Check color contrast with DevTools

---

## Tips & Best Practices

1. **Start Small** - Test with `make tiny` before large images
2. **Storage** - Budget 2-3x source image size for tiles
3. **Quality** - 90 is optimal (balance size/quality), 95 for diagnostic/medical
4. **Tile Size** - 256=smooth zoom, 512=faster load (75% fewer tiles)
5. **Medical Images** - Use QUALITY=95 TILE_SIZE=512 for diagnostic review
6. **Batch Processing** - Use shell loops for multiple images
7. **Gallery** - Auto-updates after conversion, run `make gallery` if needed
8. **Accessibility** - Test with keyboard only before deploying
9. **DICOM Limits** - Single-frame 2D only (extract slices from 3D volumes first)
10. **View While Generating** - Can view existing images while new ones generate

---

## Use Cases

- **VA Medical Imaging** - Pathology slides, X-rays, CT/MRI slices (508 compliant)
- **Digital Museums** - High-res artwork, historical documents (accessible)
- **Document Archives** - Scanned blueprints, maps, manuscripts
- **Satellite/GIS** - Map exploration, terrain visualization
- **Scientific Visualization** - Microscopy, astronomy, research data
- **Photography** - Gigapixel panoramas, aerial photography
- **Architecture** - Building plans, technical drawings
- **Education** - Accessible learning materials with deep zoom

---

## Resources

- [OpenSeadragon Website](https://openseadragon.github.io/)
- [OpenSeadragon Documentation](https://openseadragon.github.io/docs/)
- [DZI Format Specification](https://docs.microsoft.com/en-us/previous-versions/windows/silverlight/dotnet-windows-silverlight/cc645077(v=vs.95))
- [pyvips Documentation](https://libvips.github.io/pyvips/)

## Tips

1. **Start Small**: Test with 10K x 8K before generating huge images

## Resources

- [OpenSeadragon Website](https://openseadragon.github.io/)
- [OpenSeadragon Documentation](https://openseadragon.github.io/docs/)
- [DZI Format Specification](https://docs.microsoft.com/en-us/previous-versions/windows/silverlight/dotnet-windows-silverlight/cc645077(v=vs.95))
- [pyvips Documentation](https://libvips.github.io/pyvips/)
- [USWDS Design System](https://designsystem.digital.gov/)
- [VA Design System](https://design.va.gov/)
- [Section 508 Standards](https://www.section508.gov/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

## License

This is a demonstration project. OpenSeadragon is BSD-licensed.

