#!/usr/bin/env python3
"""
Generate index.html with a gallery of all available DZI images
Detects single images and multi-frame series
"""

import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import shutil
import re

def parse_dzi_info(dzi_path):
    """Extract image info from DZI file"""
    try:
        tree = ET.parse(dzi_path)
        root = tree.getroot()
        
        # DZI files use the Deep Zoom namespace
        namespace = {'dzi': 'http://schemas.microsoft.com/deepzoom/2008'}
        size = root.find('dzi:Size', namespace)
        
        if size is None:
            # Try without namespace as fallback
            size = root.find('Size')
        
        if size is None:
            print(f"Warning: No Size element in {dzi_path}")
            return None, None
            
        width = int(size.get('Width'))
        height = int(size.get('Height'))
        return width, height
    except Exception as e:
        print(f"Warning: Failed to parse DZI {dzi_path}: {e}")
        return None, None

def get_file_size(path):
    """Get human-readable file size"""
    size = os.path.getsize(path)
    return get_file_size_from_bytes(size)

def get_file_size_from_bytes(size):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def count_tiles(tiles_dir):
    """Count total tiles in directory and return count + total size"""
    if not os.path.exists(tiles_dir):
        return 0, 0
    count = 0
    total_size = 0
    for root, dirs, files in os.walk(tiles_dir):
        for f in files:
            if f.endswith('.jpg'):
                count += 1
                total_size += os.path.getsize(os.path.join(root, f))
    return count, total_size

def get_dzi_files():
    """Scan dzi/ directory and collect info about all DZI files and multi-frame series"""
    dzi_dir = Path('../output/dzi')
    if not dzi_dir.exists():
        return [], []
    
    # Find all series metadata files
    series_files = list(dzi_dir.glob('*_series.json'))
    series_data = []
    series_base_names = set()
    
    for series_file in series_files:
        try:
            with open(series_file) as f:
                metadata = json.load(f)
                series_base_names.add(metadata['base_name'])
                
                # Get first frame for preview dimensions
                first_frame_dzi = dzi_dir / f"{metadata['base_name']}_frame_0000.dzi"
                width, height = parse_dzi_info(first_frame_dzi) if first_frame_dzi.exists() else (None, None)
                
                series_data.append({
                    'filename': metadata['base_name'],
                    'is_series': True,
                    'total_frames': metadata['total_frames'],
                    'converted_frames': metadata['converted_frames'],
                    'modality': metadata['metadata'].get('modality', 'Unknown'),
                    'study': metadata['metadata'].get('study_description', 'N/A'),
                    'width': width,
                    'height': height,
                    'megapixels': (width * height / 1_000_000) if width and height else 0,
                    'tile_size': metadata.get('tile_size', 256),
                    'quality': metadata.get('quality', 90),
                    'series_file': series_file.name
                })
        except Exception as e:
            print(f"Warning: Failed to parse series file {series_file}: {e}")
    
    # Find single DZI files (not part of a series)
    dzi_files = []
    for dzi_file in sorted(dzi_dir.glob('*.dzi'), key=os.path.getmtime, reverse=True):
        base_name = dzi_file.stem
        
        # Skip if it's part of a multi-frame series
        # Check for pattern: basename_frame_NNNN
        if re.match(r'.*_frame_\d{4}$', base_name):
            continue
        
        # Skip if this base name has a series file
        if base_name in series_base_names:
            continue
        
        # Parse DZI for dimensions
        width, height = parse_dzi_info(dzi_file)
        
        # Get tiles info
        tiles_dir = dzi_dir / f"{base_name}_files"
        tile_count, tiles_size = count_tiles(tiles_dir)
        tiles_size_str = get_file_size_from_bytes(tiles_size) if tiles_size > 0 else "N/A"
        
        # Get file modification time
        mtime = os.path.getmtime(dzi_file)
        mod_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Extract timestamp from filename if present
        filename = base_name
        
        dzi_files.append({
            'filename': filename,
            'is_series': False,
            'path': f'dzi/{dzi_file.name}',
            'width': width,
            'height': height,
            'megapixels': (width * height / 1_000_000) if width and height else 0,
            'tiles_size': tiles_size_str,
            'tile_count': tile_count,
            'modified': mod_date
        })
    
    return dzi_files, series_data

def generate_index_html():
    """Generate index.html with gallery of DZI files and multi-frame series"""
    
    print("Scanning for DZI files...")
    dzi_files, series_data = get_dzi_files()
    
    total_items = len(dzi_files) + len(series_data)
    if total_items == 0:
        print("No DZI files found in ../output/dzi/ directory")
        print("Generate some with: ./create_and_convert.sh")
        return False
    
    print(f"Found {len(dzi_files)} single image(s) and {len(series_data)} series")
    
    # Generate HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Gallery</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #f0f0f0;
            min-height: 100vh;
            line-height: 1.5;
        }
        
        .header {
            background: #162e51;
            color: white;
            padding: 2rem;
            border-bottom: 4px solid #005ea2;
        }
        
        .header h1 {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            text-align: center;
            color: #dfe1e2;
            font-size: 1.125rem;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }
        
        .stats {
            background: white;
            border: 1px solid #dfe1e2;
            border-radius: 0.25rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 1.5rem;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #005ea2;
        }
        
        .stat-label {
            color: #565c65;
            margin-top: 0.5rem;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }
        
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: white;
            border: 1px solid #dfe1e2;
            border-radius: 0.25rem;
            overflow: hidden;
            transition: box-shadow 0.2s;
        }
        
        .card:hover {
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }
        
        /* Skip link for 508 compliance */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 0;
            background: #005ea2;
            color: white;
            padding: 8px;
            text-decoration: none;
            z-index: 100;
        }
        
        .skip-link:focus {
            top: 0;
        }
        
        .card-header {
            background: #005ea2;
            padding: 1.25rem;
            color: white;
            border-bottom: 1px solid #0050d8;
        }
        
        .card-title {
            font-size: 1.125rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            word-break: break-word;
        }
        
        .card-subtitle {
            font-size: 0.875rem;
            color: #dfe1e2;
        }
        
        .card-body {
            padding: 1.25rem;
        }
        
        dl {
            margin: 0;
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .info-row:last-child {
            border-bottom: none;
        }
        
        dt, dd {
            margin: 0;
        }
        
        .info-label {
            color: #565c65;
            font-weight: 600;
            font-size: 0.875rem;
        }
        
        .info-value {
            color: #1c1c1c;
            font-weight: 700;
        }
        
        .card-footer {
            padding: 1rem 1.25rem;
            background: #f0f0f0;
            border-top: 1px solid #dfe1e2;
            text-align: center;
        }
        
        .view-button {
            display: inline-block;
            background: #005ea2;
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 0.25rem;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.875rem;
            transition: background-color 0.2s;
        }
        
        .view-button:hover {
            background: #0050d8;
            text-decoration: underline;
        }
        
        .view-button:focus {
            outline: 2px solid #2491ff;
            outline-offset: 2px;
        }
        
        .megapixel-badge {
            display: inline-block;
            background: #71767a;
            color: white;
            padding: 0.25rem 0.625rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 700;
            margin-left: 0.5rem;
        }
        
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            background: white;
            border: 1px solid #dfe1e2;
            border-radius: 0.25rem;
        }
        
        .empty-state h2 {
            color: #1c1c1c;
            margin-bottom: 1rem;
            font-weight: 700;
        }
        
        .empty-state p {
            color: #565c65;
            font-size: 1.125rem;
        }
        
        .footer {
            text-align: center;
            padding: 2rem;
            color: #71767a;
            font-size: 0.875rem;
        }
        
        @media (max-width: 768px) {
            .gallery {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <!-- Skip Navigation Link for 508 Compliance -->
    <a href="#main-content" class="skip-link">Skip to main content</a>
    
    <header class="header" role="banner">
        <h1>Deep Zoom Image Gallery</h1>
        <p>High-resolution image viewer</p>
    </header>
    
    <main id="main-content" role="main">
    <div class="container">
"""
    
    if total_items > 0:
        # Calculate stats
        total_images = len(dzi_files)
        total_series_count = len(series_data)
        total_megapixels = sum(f['megapixels'] for f in dzi_files) + sum(s['megapixels'] for s in series_data)
        total_tiles = sum(f['tile_count'] for f in dzi_files)
        
        html += f"""
        <section class="stats" aria-label="Gallery Statistics">
            <div class="stat">
                <div class="stat-value" aria-label="Number of single images">{total_images}</div>
                <div class="stat-label" aria-hidden="true">Single Images</div>
            </div>
            <div class="stat">
                <div class="stat-value" aria-label="Number of series">{total_series_count}</div>
                <div class="stat-label" aria-hidden="true">Multi-Frame Series</div>
            </div>
            <div class="stat">
                <div class="stat-value" aria-label="Total megapixels">{total_megapixels:.1f}</div>
                <div class="stat-label" aria-hidden="true">Total Megapixels</div>
            </div>
        </section>
        
        <section class="gallery" aria-label="Image Gallery">
"""
        
        # Generate cards for multi-frame series first
        for series in series_data:
            megapixels = series['megapixels']
            mp_label = f"{megapixels:.1f} MP" if megapixels < 1000 else f"{megapixels/1000:.2f} GP"
            
            width_str = f"{series['width']:,}" if series['width'] else "N/A"
            height_str = f"{series['height']:,}" if series['height'] else "N/A"
            dimensions_str = f"{width_str} × {height_str} per frame" if series['width'] and series['height'] else "Dimensions unknown"
            
            html += f"""
            <article class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        📹 {series['filename']}
                        <span class="megapixel-badge" aria-label="{mp_label}">{mp_label}</span>
                    </h2>
                    <div class="card-subtitle">
                        {dimensions_str}
                    </div>
                </div>
                <div class="card-body">
                    <dl>
                        <div class="info-row">
                            <dt class="info-label">Type</dt>
                            <dd class="info-value">Multi-Frame Series</dd>
                        </div>
                        <div class="info-row">
                            <dt class="info-label">Frames</dt>
                            <dd class="info-value">{series['converted_frames']} frames</dd>
                        </div>
                        <div class="info-row">
                            <dt class="info-label">Modality</dt>
                            <dd class="info-value">{series['modality']}</dd>
                        </div>
                        <div class="info-row">
                            <dt class="info-label">Study</dt>
                            <dd class="info-value">{series['study'] if series['study'] else 'N/A'}</dd>
                        </div>
                    </dl>
                </div>
                <div class="card-footer">
                    <a href="multiframe_viewer.html?series={series['filename']}" class="view-button" aria-label="View multi-frame series: {series['filename']}">
                        ▶ View Series
                    </a>
                </div>
            </article>
"""
        
        # Generate cards for each DZI file
        for dzi in dzi_files:
            megapixels = dzi['megapixels']
            mp_label = f"{megapixels:.1f} MP" if megapixels < 1000 else f"{megapixels/1000:.2f} GP"
            
            # Handle missing dimensions
            width_str = f"{dzi['width']:,}" if dzi['width'] else "N/A"
            height_str = f"{dzi['height']:,}" if dzi['height'] else "N/A"
            dimensions_str = f"{width_str} × {height_str} pixels" if dzi['width'] and dzi['height'] else "Dimensions unknown"
            
            html += f"""
            <article class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        {dzi['filename']}
                        <span class="megapixel-badge" aria-label="{mp_label}">{mp_label}</span>
                    </h2>
                    <div class="card-subtitle">
                        {dimensions_str}
                    </div>
                </div>
                <div class="card-body">
                    <dl>
                        <div class="info-row">
                            <dt class="info-label">Created</dt>
                            <dd class="info-value">{dzi['modified']}</dd>
                        </div>
                        <div class="info-row">
                            <dt class="info-label">Tiles Size</dt>
                            <dd class="info-value">{dzi['tiles_size']}</dd>
                        </div>
                        <div class="info-row">
                            <dt class="info-label">Tile Count</dt>
                            <dd class="info-value">{dzi['tile_count']:,}</dd>
                        </div>
                    </dl>
                </div>
                <div class="card-footer">
                    <a href="viewer.html?image={dzi['path']}" class="view-button" aria-label="View image: {dzi['filename']}">
                        View Image
                    </a>
                </div>
            </article>
"""
        
        html += """
        </section>
"""
    else:
        html += """
        <div class="empty-state">
            <h2>No Images Yet</h2>
            <p>Generate your first deep zoom image with:</p>
            <code>cd src && ./create_and_convert.sh</code>
        </div>
"""
    
    html += """
    </div>
    </main>
    
    <footer class="footer" role="contentinfo">
        <p>Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        <p>OpenSeadragon Deep Zoom Gallery</p>
    </footer>
</body>
</html>
"""
    
    if not os.path.exists('../output'):
        os.makedirs('../output')
    output_path = '../output/index.html'
    with open(output_path, 'w') as f:
        f.write(html)
    
    # Copy viewer.html to output/ if it exists in root
    viewer_source = '../viewer.html'
    viewer_dest = '../output/viewer.html'
    if os.path.exists(viewer_source):
        shutil.copy2(viewer_source, viewer_dest)
        print(f"  Copied viewer.html to output/")
    
    # Copy multiframe_viewer.html to output/
    multiframe_source = '../multiframe_viewer.html'
    multiframe_dest = '../output/multiframe_viewer.html'
    if os.path.exists(multiframe_source):
        shutil.copy2(multiframe_source, multiframe_dest)
        print(f"  Copied multiframe_viewer.html to output/")
    
    print(f"\n✓ Generated index.html")
    print(f"  Location: {os.path.abspath(output_path)}")
    print(f"  Single images: {len(dzi_files)}, Multi-frame series: {len(series_data)}, Total: {total_items}")
    print(f"\nTo view: python3 -m http.server 8000")
    print("Then open: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    generate_index_html()
