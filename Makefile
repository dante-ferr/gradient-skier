.PHONY: help build run test-map test-map-3d test-map-both

# Set a default goal so that running `make` without arguments shows the help message.
DEFAULT_GOAL := help

build:
	@echo "--- Installing Dependencies ---"
	poetry install

run:
	@echo "--- Running Main Application ---"
	poetry run python src/main.py

test-map:
	@echo "--- Running Map Generation Visual Test (2D) ---"
	poetry run python src/test_and_plot_map.py

test-map-3d:
	@echo "--- Running Map Generation Visual Test (3D) ---"
	poetry run python src/test_and_plot_map.py --plot3d

test-map-all:
	@echo "--- Running Map Generation Visual Test (Side-by-Side) ---"
	poetry run python src/test_and_plot_map.py --plot-all