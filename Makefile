.PHONY: venv install lint format type test ci docs clean

VENV?=.venv

venv:
	python3 -m venv $(VENV) || python3 -m venv --without-pip $(VENV) && curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py && $(VENV)/bin/python get-pip.py

install: venv
	$(VENV)/bin/pip install -U pip
	$(VENV)/bin/pip install -e ".[dev,docs,full]"

lint:
	$(VENV)/bin/ruff check .

format:
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/black .

type:
	$(VENV)/bin/mypy penin

test:
	$(VENV)/bin/pytest -q

ci: lint type test

docs:
	$(VENV)/bin/mkdocs build --strict

clean:
	rm -rf .ruff_cache .mypy_cache .pytest_cache htmlcov site
