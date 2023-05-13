.PHONY: all setup tests dist
# make tests >debug.log 2>&1

ifeq ($(OS),Windows_NT)
PYTHON = venv/Scripts/python.exe
else
PYTHON = ./venv/bin/python
endif

SOURCE = tester_vbot3
PIP = $(PYTHON) -m pip install
PYLINT = $(PYTHON) -m pylint
FLAKE8 = $(PYTHON) -m flake8
PEP257 = $(PYTHON) -m pydocstyle

all: tests

tests: flake8 pep257 lint

flake8:
	$(FLAKE8) $(SOURCE)

lint:
	$(PYLINT) $(SOURCE)

pep257:
	$(PEP257) $(SOURCE)

package:
	$(PYTHON) -m build -n

pypitest: package
	$(PYTHON) -m twine upload --config-file .pypirc --repository testpypi dist/*

pypi: package
	$(PYTHON) -m twine upload --config-file .pypirc dist/*

setup: setup_python setup_pip

setup_pip:
	$(PIP) --upgrade pip
	$(PIP) -r requirements.txt
	$(PIP) -r tests.txt
	$(PIP) -r deploy.txt

setup_python:
	$(PYTHON_BIN) -m venv ./venv
