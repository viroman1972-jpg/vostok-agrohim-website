.PHONY: build check test
build:
	python3 -I scripts/build.py
check: build
	python3 -I scripts/check.py
test:
	python3 -I scripts/check.py --selftest
