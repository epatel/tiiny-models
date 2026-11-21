.PHONY: help fetch digest media build serve check

help:  ## List targets
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-8s %s\n", $$1, $$2}'

fetch:  ## Look all store models up on Hugging Face (data/hf.json, .cache/readme/)
	python3 scripts/fetch_hf.py

digest:  ## Print card text + media links (after fetch), to write descriptions / pick samples
	python3 scripts/card_digest.py

media:  ## Download samples from data/media.json into media/ (FORCE=1 to redo)
	scripts/media.sh

build:  ## Build index.html
	python3 scripts/build.py

serve: build  ## Build and preview at http://localhost:8000
	python3 -m http.server 8000

check:  ## Every store model has a description, aliases and metrics files are valid JSON
	@python3 -c 'import json,glob; [json.load(open(f)) for f in glob.glob("data/*.json")+glob.glob("data/metrics/*.json")]; print("json ok")'
	@python3 scripts/build.py | grep -v '^index.html' || true
