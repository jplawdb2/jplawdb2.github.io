.PHONY: build build-phase1 validate test-cite-key clean ci

build:
	python3 tools/build.py

build-phase1:
	python3 tools/build.py --phase 1

validate:
	python3 tools/validate.py

test-cite-key:
	python3 tools/test_cite_key.py

clean:
	rm -rf text/ meta/

# GitHub Actions用
ci: build-phase1 validate
