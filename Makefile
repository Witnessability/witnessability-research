PYTHON ?= python3
RUN_DIR ?= runs/development-local
export PYTHONPATH := $(CURDIR)/src

.PHONY: check check-standalone run replay all
check:
	$(PYTHON) -m unittest discover -s tests -v

CHECK_DIR ?= runs/checker-ci
check-standalone:
	$(PYTHON) -m unittest discover -s scripts/tests -v
	$(PYTHON) scripts/check_standalone.py --output $(CHECK_DIR)

run:
	$(PYTHON) -m witnessability_research run --output $(RUN_DIR)

replay:
	$(PYTHON) -m witnessability_research verify-run $(RUN_DIR)

all: check run replay
