.DEFAULT_GOAL := all

.PHONY:
install-docs: install-package
	pip install -r docs/requirements.txt

.PHONY: install-linting
install-linting:
	pip install -r tests/requirements-linting.txt

.PHONY: install-package
install-package:
	pip install -U build pip wheel
	pip install -e .

.PHONY: install-devel
install-devel:
	pip install -r tests/requirements-devel.txt

.PHONY: install-testing
install-testing: install-package
	pip install -r tests/requirements-testing.txt

.PHONY: install
install: install-devel install-docs install-testing install-linting
	@echo 'Installed development requirements'

.PHONY: build
build:
	python -m build --wheel --sdist

.PHONY: htmldoc
htmldoc:
	$(MAKE) -C docs/ html

.PHONY: format
format:
	ruff check --select=I --fix-only
	ruff format

.PHONY: lint
lint:
	ruff check
	ruff format --check --diff

.PHONY: mypy
mypy:
	mypy

.PHONY: test
test:
	pytest

.PHONY: testcov
testcov: test
	@echo "building coverage html"
	@coverage html

.PHONY: all
all: lint mypy testcov

.PHONY: clean
clean:
	$(MAKE) -C docs/ clean
	$(RM) .coverage
	$(RM) .coverage.*
	$(RM) -r *.egg-info
	$(RM) -r .mypy_cache
	$(RM) -r .pytest_cache
	$(RM) -r build
	$(RM) -r dist
	$(RM) -r htmlcov
	find aio_ld2410 tests -name '*.py[cod]' -delete
	ruff clean
