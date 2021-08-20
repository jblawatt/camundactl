#!/usr/bin/env make

PY_RUN=poetry run 
PROJECT_ROOT=camundactl

format:
	$(PY_RUN) isort $(PROJECT_ROOT)
	$(PY_RUN) black $(PROJECT_ROOT)

lint:
	$(PY_RUN) mypy $(PROJECT_ROOT)
	$(PY_RUN) flake8 $(PROJECT_ROOT)


docs:
	$(PY_RUN) mkdocs serve


test:
	$(PY_RUN) pytest --cov-report=html --cov-report=term .
	