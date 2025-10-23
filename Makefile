test_map:
	@echo "--- Running Map Generation Visual Test ---"
	poetry run python src/test_and_plot_map.py
	@echo "--- Test Complete ---"

build:
	poetry install

run:
	poetry run python src/main.py