.PHONY: run install dist

run:
	pipenv run python -m lidske_aktivity

install:
	sudo pacman -S gobject-introspection

dist:
	@echo "TODO"
