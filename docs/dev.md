# Development

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run tests
```bash
pytest -q
```

## Lint / format (optional)
```bash
python -m ruff check .
python -m ruff format .
```

## Notes about TestY dependency
This repo starts with unit-testable components (parser/sanitize/mapping) that do NOT require TestY installed.
Integration modules (DRF views, pluggy hooks, importer using TestY services) should be implemented behind adapters
or with conditional imports so unit tests remain runnable.

