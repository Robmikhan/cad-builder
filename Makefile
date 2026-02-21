.PHONY: dev worker test fmt lint

dev:
	bash scripts/run_dev.sh

worker:
	bash scripts/run_worker.sh

test:
	python -m pytest -q

fmt:
	python -m ruff format .

lint:
	python -m ruff check .
