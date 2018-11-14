.PHONY: run install dist clean

run:
	pipenv run python -m lidske_aktivity

install:
	sudo pacman -S gobject-introspection

dist:
	@echo "TODO"

clean:
	-rm lidske_aktivity/cache.csv
