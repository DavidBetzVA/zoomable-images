#!/usr/bin/env python3
"""
Convert DICOM images to Deep Zoom Image (DZI) tiles
Handles single-frame and multi-frame DICOM medical imaging

Usage:
    python3 convert_dicom_to_dzi.py scan.dcm
    python3 convert_dicom_to_dzi.py scan.dcm patient_001
    python3 convert_dicom_to_dzi.py scan.dcm patient_001 --tile-size 512 --quality 95
    python3 convert_dicom_to_dzi.py multi.dcm study --all-frames
    python3 convert_dicom_to_dzi.py multi.dcm study --frame 50
"""

import sys
import os
from pathlib import Path
import argparse
import tempfile

try:
    import pydicom
except ImportError:
    print("❌ Error: pydicom not installed")
    print("   Install with: pip install pydicom")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("❌ Error: numpy not installed")
    print("   Install with: pip install numpy")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("❌ Error: Pillow not installed")
    print("   Install with: pip install pillow")
    sys.exit(1)

try:
    import pyvips
except ImportError:
    print("❌ Error: pyvips not installed")
    print("   Install with: pip install pyvips")
    sys.exit(1)

def format_bytes(bytes_val):
    """Human-readable file size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

def dicom_to_image(dicom_path, frame_index=None):
    """
    Convert DICOM file to PIL Image
    Handles windowing, rescaling, normalization, and multi-frame extraction
    
    Args:
        dicom_path: Path to DICOM file
        frame_index: For multi-frame DICOM, extract specific frame (0-indexed). None = single frame expected
    
    Returns:
        (image, dicom_dataset, total_frames) tuple
    """
    # Read DICOM file
    ds = pydicom.dcmread(dicom_path)
    
    # Get pixel array
    pixel_array = ds.pixel_array
    original_shape = pixel_array.shape
    
    # Determine if multi-frame
    total_frames = 1
    if len(pixel_array.shape) == 3:
        # Could be multi-frame (N, H, W) or single-frame RGB (H, W, 3)
        if pixel_array.shape[2] == 3:
            # RGB color image (H, W, 3)
            pass
        else:
            # Multi-frame (N, H, W)
            total_frames = pixel_array.shape[0]
            if frame_index is not None:
                if frame_index < 0 or frame_index >= total_frames:
                    raise ValueError(f"Frame index {frame_index} out of range (0-{total_frames-1})")
                pixel_array = pixel_array[frame_index]
            elif total_frames == 1:
                pixel_array = pixel_array[0]
            else:
                # Multi-frame without specific frame requested - return info for user
                return None, ds, total_frames
    
    # Remove any remaining single dimensions
    pixel_array = np.squeeze(pixel_array)
    
    # Ensure we have a valid 2D image
    if len(pixel_array.shape) == 1:
        # 1D array - unsupported format
        raise ValueError(
            f"❌ Invalid DICOM image dimensions.\n"
            f"   Original shape: {original_shape}\n"
            f"   After squeeze: {pixel_array.shape}\n"
            f"   This appears to be a 1D array, not a 2D image.\n"
            f"   Supported: Single-frame 2D DICOM images only.\n"
            f"   Not supported: Waveforms, spectroscopy, or multi-frame DICOM."
        )
    elif len(pixel_array.shape) == 3:
        # 3D volume - check if it's multi-frame or has color channels
        if pixel_array.shape[0] > 1 and pixel_array.shape[2] != 3:
            # Multi-frame/3D volume (e.g., 96 slices of 512x512)
            raise ValueError(
                f"❌ Unsupported DICOM format: Multi-frame/3D volume.\n"
                f"   Shape: {pixel_array.shape} ({pixel_array.shape[0]} frames/slices of {pixel_array.shape[1]}×{pixel_array.shape[2]})\n"
                f"   Supported: Single-frame 2D images only.\n"
                f"   \n"
                f"   To convert this volume:\n"
                f"   1. Extract individual slices using DICOM tools\n"
                f"   2. Convert each slice separately\n"
                f"   3. Or use specialized 3D medical imaging software"
            )
    elif len(pixel_array.shape) > 3:
        raise ValueError(
            f"❌ Unsupported DICOM dimensions: {pixel_array.shape}.\n"
            f"   Supported: Single-frame 2D images only.\n"
            f"   For 3D/4D data, please extract individual slices first."
        )
    
    # Apply rescale slope and intercept if present (Hounsfield units for CT)
    if hasattr(ds, 'RescaleSlope') and hasattr(ds, 'RescaleIntercept'):
        pixel_array = pixel_array * ds.RescaleSlope + ds.RescaleIntercept
    
    # Apply windowing if WindowCenter and WindowWidth are present
    if hasattr(ds, 'WindowCenter') and hasattr(ds, 'WindowWidth'):
        window_center = ds.WindowCenter
        window_width = ds.WindowWidth
        
        # Handle multiple windows (use first)
        if isinstance(window_center, (list, pydicom.multival.MultiValue)):
            window_center = float(window_center[0])
        if isinstance(window_width, (list, pydicom.multival.MultiValue)):
            window_width = float(window_width[0])
        
        # Apply window
        img_min = window_center - window_width / 2
        img_max = window_center + window_width / 2
        pixel_array = np.clip(pixel_array, img_min, img_max)
    
    # Normalize to 0-255 range
    pixel_array = pixel_array - np.min(pixel_array)
    if np.max(pixel_array) > 0:  # Avoid division by zero
        pixel_array = pixel_array / np.max(pixel_array)
    pixel_array = (pixel_array * 255).astype(np.uint8)
    
    # Handle photometric interpretation
    photometric = getattr(ds, 'PhotometricInterpretation', 'MONOCHROME2')
    if photometric == 'MONOCHROME1':
        # Invert for MONOCHROME1 (pixel value increases = darker)
        pixel_array = 255 - pixel_array
    
    # Convert to PIL Image
    if len(pixel_array.shape) == 2:
        # Grayscale
        image = Image.fromarray(pixel_array, mode='L')
    else:
        # Color (RGB)
        image = Image.fromarray(pixel_array, mode='RGB')
    
    return image, ds, total_frames

def extract_dicom_metadata(ds):
    """Extract useful metadata from DICOM dataset"""
    metadata = {}
    
    # Patient info
    metadata['patient_id'] = getattr(ds, 'PatientID', 'Unknown')
    metadata['patient_name'] = str(getattr(ds, 'PatientName', 'Unknown'))
    
    # Study info
    metadata['study_date'] = getattr(ds, 'StudyDate', 'Unknown')
    metadata['study_description'] = getattr(ds, 'StudyDescription', 'Unknown')
    metadata['modality'] = getattr(ds, 'Modality', 'Unknown')
    
    # Image info
    metadata['rows'] = getattr(ds, 'Rows', 0)
    metadata['columns'] = getattr(ds, 'Columns', 0)
    metadata['bits_stored'] = getattr(ds, 'BitsStored', 0)
    metadata['photometric'] = getattr(ds, 'PhotometricInterpretation', 'Unknown')
    
    return metadata

def convert_dicom_to_dzi(dicom_path, output_name=None, tile_size=256, quality=90, overlap=1):
    """
    Convert DICOM image to DZI format
    
    Args:
        dicom_path: Path to DICOM file (.dcm)
        output_name: Optional custom output name
        tile_size: Size of each tile (default 256)
        quality: JPEG quality 1-100 (default 90)
        overlap: Pixel overlap between tiles (default 1)
    """
    dicom_path = Path(dicom_path)
    
    # Validate input
    if not dicom_path.exists():
        print(f"❌ Error: File not found: {dicom_path}")
        return False
    
    # Determine output name
    if output_name:
        base_name = output_name
    else:
        base_name = dicom_path.stem
    
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
    print(f"Converting DICOM: {dicom_path.name}")
    print(f"Output: {base_name}.dzi")
    print(f"{'='*60}\n")
    
    # Get input file info
    input_size = dicom_path.stat().st_size
    print(f"📁 DICOM file: {format_bytes(input_size)}")
    
    try:
        # Read and convert DICOM
        print(f"🏥 Reading DICOM file...")
        image, dicom_dataset, total_frames = dicom_to_image(dicom_path)
        
        # Check if multi-frame
        if image is None and total_frames > 1:
            print(f"\n📹 Multi-frame DICOM detected: {total_frames} frames")
            print(f"   Use --all-frames to convert all frames")
            print(f"   Use --frame N to convert specific frame (0-{total_frames-1})")
            return False
        
        # Extract metadata
        metadata = extract_dicom_metadata(dicom_dataset)
        
        print(f"\n📊 DICOM Metadata:")
        print(f"   Modality: {metadata['modality']}")
        print(f"   Patient ID: {metadata['patient_id']}")
        print(f"   Study Date: {metadata['study_date']}")
        print(f"   Study: {metadata['study_description']}")
        print(f"   Photometric: {metadata['photometric']}")
        print(f"   Bit Depth: {metadata['bits_stored']} bits")
        
        # Image info
        width, height = image.size
        megapixels = (width * height) / 1_000_000
        
        print(f"\n📐 Image Dimensions: {width:,} × {height:,} pixels")
        print(f"🖼️  Megapixels: {megapixels:.1f} MP")
        print(f"🎨 Mode: {image.mode}")
        
        print(f"\n🔧 Tile size: {tile_size}×{tile_size}")
        print(f"📊 Quality: {quality}")
        print(f"🔗 Overlap: {overlap}px")
        
        # Save to temporary file
        print(f"\n⚙️  Converting to DZI format...")
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            temp_path = tmp_file.name
            image.save(temp_path, 'PNG')
        
        try:
            # Convert to DZI using pyvips
            vips_image = pyvips.Image.new_from_file(temp_path)
            vips_image.dzsave(
                str(dzi_path.with_suffix('')),
                tile_size=tile_size,
                overlap=overlap,
                suffix='.jpg[Q={0}]'.format(quality),
                depth='onepixel',
                centre=False,
                layout='dz'
            )
        finally:
            # Clean up temp file
            os.unlink(temp_path)
        
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
        import traceback
        traceback.print_exc()
        return False

def convert_dicom_multiframe(dicom_path, output_name=None, tile_size=256, quality=90, overlap=1, frame_number=None):
    """
    Convert multi-frame DICOM to DZI format
    
    Args:
        dicom_path: Path to multi-frame DICOM file
        output_name: Base name for output files
        tile_size: Size of each tile
        quality: JPEG quality
        overlap: Pixel overlap
        frame_number: Specific frame to convert (0-indexed), or None for all frames
    """
    dicom_path = Path(dicom_path)
    
    if not dicom_path.exists():
        print(f"❌ Error: File not found: {dicom_path}")
        return False
    
    # Determine base name
    if output_name:
        base_name = output_name
    else:
        base_name = dicom_path.stem
    
    output_dir = Path('../output/dzi')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Converting Multi-Frame DICOM: {dicom_path.name}")
    print(f"{'='*60}\n")
    
    input_size = dicom_path.stat().st_size
    print(f"📁 DICOM file: {format_bytes(input_size)}")
    
    try:
        # First check total frames
        print(f"🏥 Reading DICOM file...")
        image, dicom_dataset, total_frames = dicom_to_image(dicom_path)
        
        if total_frames == 1:
            print(f"⚠️  This is a single-frame DICOM. Use regular convert_dicom_to_dzi instead.")
            return False
        
        print(f"📹 Total frames: {total_frames}")
        
        # Extract metadata once
        metadata = extract_dicom_metadata(dicom_dataset)
        print(f"   Modality: {metadata['modality']}")
        print(f"   Patient ID: {metadata['patient_id']}")
        print(f"   Study: {metadata['study_description']}")
        
        # Determine which frames to convert
        if frame_number is not None:
            frames_to_convert = [frame_number]
            print(f"\n🎯 Converting frame {frame_number} of {total_frames}")
        else:
            frames_to_convert = list(range(total_frames))
            print(f"\n🎯 Converting all {total_frames} frames...")
        
        converted_count = 0
        failed_count = 0
        
        for frame_idx in frames_to_convert:
            frame_name = f"{base_name}_frame_{frame_idx:04d}"
            dzi_path = output_dir / f"{frame_name}.dzi"
            tiles_dir = output_dir / f"{frame_name}_files"
            
            # Check if already exists
            if dzi_path.exists():
                print(f"   ⏭️  Frame {frame_idx}: Already exists, skipping...")
                continue
            
            try:
                # Extract this frame
                frame_image, _, _ = dicom_to_image(dicom_path, frame_index=frame_idx)
                
                # Convert to temporary PNG
                temp_png = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                frame_image.save(temp_png.name)
                
                # Convert PNG to DZI
                vips_image = pyvips.Image.new_from_file(temp_png.name)
                vips_image.dzsave(
                    str(dzi_path.with_suffix('')),
                    tile_size=tile_size,
                    overlap=overlap,
                    suffix=f'.jpg[Q={quality}]'
                )
                
                # Clean up temp file
                os.unlink(temp_png.name)
                
                converted_count += 1
                if converted_count % 10 == 0:
                    print(f"   ✅ Converted {converted_count}/{len(frames_to_convert)} frames...")
                
            except Exception as e:
                print(f"   ❌ Frame {frame_idx} failed: {e}")
                failed_count += 1
        
        print(f"\n✅ Multi-frame conversion complete!")
        print(f"   Converted: {converted_count} frames")
        if failed_count > 0:
            print(f"   Failed: {failed_count} frames")
        
        # Create a series metadata file
        series_file = output_dir / f"{base_name}_series.json"
        import json
        series_data = {
            "base_name": base_name,
            "total_frames": total_frames,
            "converted_frames": converted_count,
            "metadata": metadata,
            "tile_size": tile_size,
            "quality": quality
        }
        with open(series_file, 'w') as f:
            json.dump(series_data, f, indent=2)
        
        print(f"\n📁 Output location:")
        print(f"   {output_dir}/{base_name}_frame_*.dzi")
        print(f"   {series_file}")
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Run: make gallery")
        print(f"   2. Open multi-frame viewer for {base_name}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Convert DICOM images to Deep Zoom Image (DZI) format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single-frame DICOM
  python3 convert_dicom_to_dzi.py xray.dcm
  python3 convert_dicom_to_dzi.py ct_slice.dcm patient_001
  
  # Multi-frame DICOM
  python3 convert_dicom_to_dzi.py angiogram.dcm study --all-frames
  python3 convert_dicom_to_dzi.py cine.dcm cardiac --frame 50
  
Supported: Single-frame 2D and multi-frame DICOM files
        """
    )
    
    parser.add_argument('input', help='Input DICOM file path (.dcm)')
    parser.add_argument('output_name', nargs='?', help='Optional output name (default: input filename)')
    parser.add_argument('--tile-size', type=int, default=256, choices=[128, 256, 512],
                       help='Tile size in pixels (default: 256)')
    parser.add_argument('--quality', type=int, default=90,
                       help='JPEG quality 1-100 (default: 90)')
    parser.add_argument('--overlap', type=int, default=1,
                       help='Pixel overlap between tiles (default: 1)')
    parser.add_argument('--all-frames', action='store_true',
                       help='Convert all frames of multi-frame DICOM')
    parser.add_argument('--frame', type=int, metavar='N',
                       help='Convert specific frame number (0-indexed) from multi-frame DICOM')
    
    args = parser.parse_args()
    
    # Validate quality
    if not 1 <= args.quality <= 100:
        print("❌ Error: Quality must be between 1 and 100")
        sys.exit(1)
    
    # Check if multi-frame options specified
    if args.all_frames or args.frame is not None:
        success = convert_dicom_multiframe(
            args.input,
            args.output_name,
            args.tile_size,
            args.quality,
            args.overlap,
            args.frame
        )
    else:
        # Regular single-frame conversion
        success = convert_dicom_to_dzi(
            args.input,
            args.output_name,
            args.tile_size,
            args.quality,
            args.overlap
        )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
