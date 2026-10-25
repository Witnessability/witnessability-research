PYTHON ?= python3
RUN_DIR ?= runs/development-local
export PYTHONPATH := $(CURDIR)/src

.PHONY: check run replay all
check:
	$(PYTHON) -m unittest discover -s tests -v

run:
	$(PYTHON) -m witnessability_research run --output $(RUN_DIR)

replay:
	$(PYTHON) -m witnessability_research verify-run $(RUN_DIR)

all: check run replay
