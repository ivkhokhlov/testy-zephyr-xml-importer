.PHONY: test lint format

test:
	pytest -q

lint:
	python -m ruff check .

format:
	python -m ruff format .
