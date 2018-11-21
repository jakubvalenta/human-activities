.PHONY: run run-debug install dist clean clean-cache test unit-test lint help

run:  ## Start the app
	pipenv run python -m lidske_aktivity

run-debug:  ## Start the app with extended logging
	pipenv run python -m lidske_aktivity --verbose

install:  ## Install required packages
	sudo pacman -S gobject-introspection

dist:  ## Build distribution package
	pipenv run pyinstaller \
		--windowed \
		--name=lidske-aktivity \
		--specpath=install \
		lidske_aktivity/__main__.py

clean:  ## Clean distribution package
	-rm -r build
	-rm -r dist

clean-cache:  ## Clean cache
	pipenv run python -m lidske_aktivity --verbose --clean

test:  ## Run unit tests and linting
	tox

unit-test:  ## Run unit tests
	tox -e py37

lint:  ## Run linting
	tox -e lint

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'
