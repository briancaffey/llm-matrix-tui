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

# Run a baseline benchmark. Override LABEL for custom output filename.
#   make bench LABEL=before-buffering
LABEL ?= baseline
bench:
	mkdir -p bench-results
	uv run python -m matrix_tui --bench 10 -c 80 --animation-preset intense \
		--bench-output bench-results/$(LABEL).json --bench-label $(LABEL)

# Run pyinstrument over the bench (writes pyinstrument.html)
profile:
	uv run pyinstrument -o pyinstrument.html -r html \
		-m matrix_tui --bench 10 -c 80 --animation-preset intense

# Compare two bench result JSONs:
#   make compare BEFORE=bench-results/a.json AFTER=bench-results/b.json
compare:
	uv run python -m matrix_tui.bench_compare $(BEFORE) $(AFTER)

# Clean up
clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
