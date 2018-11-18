.PHONY: run install dist clean test lint help

run:
	pipenv run python -m lidske_aktivity

install:
	sudo pacman -S gobject-introspection

dist:
	@echo "TODO"

clean:
	-rm lidske_aktivity/cache.csv

test:
	tox

lint:
	tox -e lint

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'
