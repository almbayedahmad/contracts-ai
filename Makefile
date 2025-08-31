PY=python
PIP=pip

setup:
	$(PIP) install -U pip
	$(PIP) install -r backend/requirements.txt
	$(PIP) install -r frontend/requirements.txt
	pre-commit install

lint:
	ruff backend/app frontend
	black --check backend/app frontend
	mypy backend/app

typecheck:
	mypy backend/app

test:
	pytest

run-api:
	$(PY) -m backend.app.main

run-ui:
	streamlit run frontend/ui_streamlit.py

e2e:
	pytest backend/tests/e2e -q

release:
	@echo $$(cat VERSION)


autoupdate:
	python scripts/auto_update.py
