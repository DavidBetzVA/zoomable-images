# OpenSeadragon Deep Zoom Image Generator - Makefile
# ==================================================

# Configuration
PYTHON := $(CURDIR)/src/env/bin/python
WIDTH ?= 50000
HEIGHT ?= 40000
OUTPUT_NAME ?=
TILE_SIZE ?= 256
QUALITY ?= 90
NICENESS ?= 19
PORT ?= 8000

# Directories
GENERATE_DIR := src
OUTPUT_DIR := output
DZI_DIR := $(OUTPUT_DIR)/dzi
LOGS_DIR := $(OUTPUT_DIR)/logs

# Phony targets
.PHONY: help tiny quick medium large extreme generate convert convert-dicom gallery view stop-server view-bg clean

# Default target
help:
	@echo "OpenSeadragon Deep Zoom Image Generator - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  tiny          - Generate a tiny test image (2000 x 2000)"
	@echo "  quick         - Generate a quick test image (5000 x 4000)"
	@echo "  medium        - Generate a medium image (50000 x 40000)"
	@echo "  large         - Generate a large image (100000 x 80000)"
	@echo "  extreme       - Generate an extreme image (200000 x 160000)"
	@echo "  generate      - Generate a custom image (set WIDTH and HEIGHT)"
	@echo "                  Optional: set OUTPUT_NAME to specify output filename"
	@echo "  convert       - Convert existing image to DZI (set INPUT)"
	@echo "                  Supports: PNG, JPG, BMP, TIFF, WEBP, GIF"
	@echo "                  Optional: set OUTPUT_NAME, TILE_SIZE, QUALITY"
	@echo "  convert-dicom - Convert DICOM medical image to DZI (set INPUT)"
	@echo "                  Supports: Single-frame 2D DICOM (.dcm)"
	@echo "                  Optional: set OUTPUT_NAME, TILE_SIZE, QUALITY"
	@echo "  gallery       - Regenerate the gallery (output/index.html)"
	@echo "  view          - Start HTTP server to view gallery"
	@echo "  stop-server   - Stop the HTTP server"
	@echo "  view-bg       - Start HTTP server in background"
	@echo "  clean         - Remove all generated DZI files and logs"
	@echo ""
	@echo "Usage examples:"
	@echo "  make tiny"
	@echo "  make generate WIDTH=60000 HEIGHT=40000 OUTPUT_NAME=my_image"
	@echo "  make convert INPUT=photo.jpg OUTPUT_NAME=my_photo"
	@echo "  make convert INPUT=scan.tiff TILE_SIZE=512 QUALITY=95"
	@echo "  make convert-dicom INPUT=xray.dcm OUTPUT_NAME=patient_001"
	@echo ""

# Quick presets
tiny:
	@echo "Generating tiny test image (2000 x 2000) for visual design..."
	cd $(GENERATE_DIR) && ./create_and_convert.sh 2000 2000
	@$(MAKE) gallery
	@echo ""
	@echo "✓ Done! Open output/index.html to view."
	@echo "To serve: make view"

quick:
	@echo "Generating quick test image (5000 x 4000)..."
	cd $(GENERATE_DIR) && ./create_and_convert.sh 5000 4000
	@$(MAKE) gallery

medium:
	@echo "Generating medium image (50000 x 40000)..."
	cd $(GENERATE_DIR) && ./create_and_convert.sh 50000 40000
	@$(MAKE) gallery

large:
	@echo "Generating large image (100000 x 80000)..."
	cd $(GENERATE_DIR) && ./create_and_convert.sh 100000 80000
	@$(MAKE) gallery

extreme:
	@echo "Generating extreme image (200000 x 160000)..."
	cd $(GENERATE_DIR) && ./create_and_convert.sh 200000 160000
	@$(MAKE) gallery

# Custom generation
generate:
	@if [ -z "$(OUTPUT_NAME)" ]; then \
		echo "Generating $(WIDTH) x $(HEIGHT) image..."; \
		cd $(GENERATE_DIR) && ./create_and_convert.sh $(WIDTH) $(HEIGHT); \
	else \
		echo "Generating $(WIDTH) x $(HEIGHT) image as '$(OUTPUT_NAME)'..."; \
		cd $(GENERATE_DIR) && ./create_and_convert.sh $(WIDTH) $(HEIGHT) $(OUTPUT_NAME); \
	fi
	@$(MAKE) gallery

convert:
	@if [ -z "$(INPUT)" ]; then \
		echo "❌ Error: INPUT is required"; \
		echo "Usage: make convert INPUT=path/to/image.jpg"; \
		echo "       make convert INPUT=photo.jpg OUTPUT_NAME=my_photo"; \
		echo "       make convert INPUT=scan.tiff TILE_SIZE=512 QUALITY=95"; \
		echo ""; \
		echo "Supported formats: PNG, JPG, BMP, TIFF, WEBP, GIF"; \
		exit 1; \
	fi
	@INPUT_ABS=$$(cd "$$(dirname "$(INPUT)")" && pwd)/$$(basename "$(INPUT)"); \
	if [ -z "$(OUTPUT_NAME)" ]; then \
		cd $(GENERATE_DIR) && $(PYTHON) convert_to_dzi.py "$$INPUT_ABS" --tile-size $(TILE_SIZE) --quality $(QUALITY); \
	else \
		cd $(GENERATE_DIR) && $(PYTHON) convert_to_dzi.py "$$INPUT_ABS" "$(OUTPUT_NAME)" --tile-size $(TILE_SIZE) --quality $(QUALITY); \
	fi
	@$(MAKE) gallery

convert-dicom:
	@if [ -z "$(INPUT)" ]; then \
		echo "❌ Error: INPUT is required"; \
		echo "Usage: make convert-dicom INPUT=path/to/scan.dcm"; \
		echo "       make convert-dicom INPUT=xray.dcm OUTPUT_NAME=patient_001"; \
		echo "       make convert-dicom INPUT=ct.dcm TILE_SIZE=512 QUALITY=95"; \
		echo "       make convert-dicom INPUT=multi.dcm FRAMES=all"; \
		echo "       make convert-dicom INPUT=multi.dcm FRAMES=50"; \
		echo ""; \
		echo "Supports: Single-frame and multi-frame DICOM files (.dcm)"; \
		exit 1; \
	fi
	@INPUT_ABS=$$(cd "$$(dirname "$(INPUT)")" && pwd)/$$(basename "$(INPUT)"); \
	EXTRA_ARGS=""; \
	if [ "$(FRAMES)" = "all" ]; then \
		EXTRA_ARGS="--all-frames"; \
	elif [ -n "$(FRAMES)" ]; then \
		EXTRA_ARGS="--frame $(FRAMES)"; \
	fi; \
	if [ -z "$(OUTPUT_NAME)" ]; then \
		cd $(GENERATE_DIR) && $(PYTHON) convert_dicom_to_dzi.py "$$INPUT_ABS" --tile-size $(TILE_SIZE) --quality $(QUALITY) $$EXTRA_ARGS; \
	else \
		cd $(GENERATE_DIR) && $(PYTHON) convert_dicom_to_dzi.py "$$INPUT_ABS" "$(OUTPUT_NAME)" --tile-size $(TILE_SIZE) --quality $(QUALITY) $$EXTRA_ARGS; \
	fi
	@$(MAKE) gallery

# Gallery management
gallery:
	@echo "Regenerating gallery (output/index.html)..."
	cd $(GENERATE_DIR) && $(PYTHON) generate_index.py
	@echo "Gallery updated: output/index.html"

# Server management
view:
	@echo "Starting HTTP server on port $(PORT)..."
	@echo "Open: http://localhost:$(PORT)/"
	@echo "Press Ctrl+C to stop"
	python3 -m http.server $(PORT) -d $(OUTPUT_DIR)

stop-server:
	@echo "Stopping HTTP server on port $(PORT)..."
	@pkill -f "http.server $(PORT)" || echo "No server running on port $(PORT)"

view-bg:
	@echo "Starting HTTP server on port $(PORT) in background..."
	@nohup python3 -m http.server $(PORT) -d $(OUTPUT_DIR) > /dev/null 2>&1 & \
	echo $$! > .server.pid
	@echo "Server started (PID: $$(cat .server.pid))"
	@echo "Open: http://localhost:$(PORT)"
	@echo "Stop with: make stop-server"

# Cleanup
clean:
	@echo "Removing all generated DZI files and logs..."
	@read -p "Are you sure? This will delete all DZI images! (y/N) " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf $(DZI_DIR)/*.dzi $(DZI_DIR)/*_files $(DZI_DIR)/*.png; \
		rm -rf $(LOGS_DIR)/*.log; \
		rm -f $(OUTPUT_DIR)/*.pid; \
		echo "Cleaned."; \
	else \
		echo "Cancelled."; \
	fi
