# ---------- config ----------
IMAGE ?= chem-autotutor:fixed
OUT   ?= $(PWD)/out

# Inputs (override on the command line, e.g. make name NAME="...")
NAME  ?= 4-bromo-3-methylhept-1-en-6-yne
SMILES?= CCC([Br]CC#C)=C
INCHI ?=

# Mounts used during dev so you don't need to rebuild after code edits
MOUNTS = -v "$(OUT):/app/out" \
         -v "$(PWD)/build.py:/app/build.py:ro" \
         -v "$(PWD)/templates:/app/templates:ro"

# ---------- targets ----------
.PHONY: build name smiles inchi formula shell clean

build:
	docker build --no-cache -t $(IMAGE) .

name:
	mkdir -p $(OUT); chmod 777 $(OUT)
	docker run --rm $(MOUNTS) $(IMAGE) \
	  python /app/build.py --name "$(NAME)"

smiles:
	mkdir -p $(OUT); chmod 777 $(OUT)
	docker run --rm $(MOUNTS) $(IMAGE) \
	  python /app/build.py --smiles "$(SMILES)"

inchi:
	mkdir -p $(OUT); chmod 777 $(OUT)
	docker run --rm $(MOUNTS) $(IMAGE) \
	  python /app/build.py --inchi "$(INCHI)"

formula:
	mkdir -p $(OUT); chmod 777 $(OUT)
	docker run --rm $(MOUNTS) $(IMAGE) \
	  python /app/build.py --formula "$(FORMULA)"

shell:
	docker run --rm -it -v "$(OUT):/app/out" $(IMAGE) bash

clean:
	rm -rf out
