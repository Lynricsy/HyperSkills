# The suite runs on the Node built-in test runner, driven from here.
# There is no npm `test` script on purpose: see CONTRIBUTING.md.
NODE ?= node
TEST_REPORTER ?= spec

.PHONY: test test-one lint

test:
	$(NODE) --test --test-reporter=$(TEST_REPORTER)

test-one:
	@test -n "$(FILE)" || { echo "usage: make test-one FILE=<name>.test.js"; exit 2; }
	$(NODE) --test --test-reporter=$(TEST_REPORTER) $(FILE)

lint:
	npm run lint
