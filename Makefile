# Format all Python code using black
black:
	uv run black src tests

# Run tests
test:
	uv run pytest

# Run the application
run:
	uv run python -m matrix_tui

# Install dependencies
install:
	uv sync

# Clean up
clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
