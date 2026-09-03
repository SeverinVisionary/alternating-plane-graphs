# Reproduction entry points.  `make verify` is the one a referee should run.
PYTHON ?= python3

.PHONY: verify verify-fast verify-all manifest figures deps deps-optional clean

## Full gate suite for the three settled conjectures (~13 min).
## Needs only pytest; optional-dependency tests skip cleanly.
verify:
	$(PYTHON) -m pytest -q

## The load-bearing certificate and conjecture gates only (~1 min).
verify-fast:
	$(PYTHON) -m pytest -q \
	  test_target_certificates.py \
	  test_conjecture_10_1.py \
	  test_conjecture_10_3.py \
	  test_pumping_splice.py \
	  test_family_connectivity.py \
	  test_connectivity.py \
	  test_section8_witnesses.py \
	  test_surgery_witnesses.py \
	  test_bridge_lemma.py \
	  test_formats.py \
	  test_manifest.py \
	  test_export_planar_code.py \
	  test_draw.py

## Everything, including the optional SAT lanes.  Requires requirements-optional.txt.
verify-all: deps-optional verify

## Re-render the committed figures from the certificates.
figures:
	@for n in 46 47 48 49 50; do \
	  $(PYTHON) draw.py certificates/targets/TARGET_$$n.json figures/TARGET_$$n.svg; \
	  $(PYTHON) draw.py certificates/targets/TARGET_$$n.json figures/TARGET_$$n.tex --tikz; \
	done

## Check every byte of evidence against certificates/MANIFEST.sha256.
manifest:
	$(PYTHON) tools_manifest.py

deps:
	$(PYTHON) -m pip install -r requirements.txt

deps-optional:
	$(PYTHON) -m pip install -r requirements-optional.txt

clean:
	rm -rf .pytest_cache
	find . -name __pycache__ -type d -exec rm -rf {} +

artifact-pdf:
	python3 render_artifact_pdf.py

.PHONY: artifact-pdf
