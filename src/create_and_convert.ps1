#!/usr/bin/env pwsh
# Quick script to generate a test image and convert it to DZI
# PowerShell version for Windows (also works on Linux/Mac with PowerShell Core)

param(
    [int]$Width = 50000,
    [int]$Height = 40000,
    [string]$OutputName = ""
)

# Use virtual environment if available
if (Test-Path "env/Scripts/python.exe") {
    $PYTHON = "env/Scripts/python.exe"
    Write-Host "Using virtual environment"
} elseif (Test-Path "env/bin/python3") {
    $PYTHON = "env/bin/python3"
    Write-Host "Using virtual environment"
} else {
    $PYTHON = "python3"
}

# Generate timestamp for unique filenames
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
if ([string]::IsNullOrEmpty($OutputName)) {
    $OutputName = "image_${Width}x${Height}_${TIMESTAMP}"
}

# Ensure dzi directory exists
if (-not (Test-Path "dzi")) {
    New-Item -ItemType Directory -Path "dzi" | Out-Null
}

Write-Host "======================================"
Write-Host "OPENSEADRAGON IMAGE GENERATOR"
Write-Host "======================================"
Write-Host "Creating ${Width}x${Height} image..."
Write-Host "Output: dzi/$OutputName"
Write-Host ""

# Generate the test image with timestamped name
$SOURCE_IMAGE = "dzi/$OutputName.png"
& $PYTHON sample_creator.py $Width $Height $SOURCE_IMAGE

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "======================================"
    Write-Host "Converting to DZI tiles..."
    Write-Host ""
    
    # Convert to DZI (output will be in dzi/ directory)
    & $PYTHON png_to_dzi.py $SOURCE_IMAGE "dzi/$OutputName"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "======================================"
        Write-Host "✓ ALL DONE!"
        Write-Host "======================================"
        Write-Host "Your OpenSeadragon tiles are ready!"
        Write-Host ""
        Write-Host "Files created:"
        Write-Host "  Source image: dzi/$OutputName.png"
        Write-Host "  DZI metadata: dzi/$OutputName.dzi"
        Write-Host "  Tiles folder: dzi/${OutputName}_files/"
        Write-Host ""
        Write-Host "To view in browser:"
        Write-Host "  1. Update index.html tileSources to: 'src/dzi/$OutputName.dzi'"
        Write-Host "  2. Run: python3 -m http.server 8000"
        Write-Host "  3. Open: http://localhost:8000"
        Write-Host ""
        Write-Host "Or list available DZI files:"
        Write-Host "  Get-ChildItem dzi/*.dzi"
        Write-Host ""
    }
}
