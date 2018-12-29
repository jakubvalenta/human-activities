_name=lidske-aktivity
_version=0.1.1
_arch_linux_pkgrel=1
_arch_linux_src_path=install/arch_linux/${_name}-${_version}.tar.xz
_arch_linux_pkg_path=install/arch_linux/${_name}-${_version}-${_arch_linux_pkgrel}-any.pkg.tar.xz

.PHONY: run run-debug dist-prepare dist dist-onefile dist-arch-linux install-arch-linux build build-data clean clean-cache test unit-test lint lint-arch-linux check help

run:  ## Start the app
	pipenv run python -m lidske_aktivity

run-debug:  ## Start the app with extended logging
	pipenv run python -m lidske_aktivity --verbose

dist-prepare:  ## Build the docker image required for packaging
	docker build -t lidske_aktivity .

dist:  ## Build distribution package
	pipenv run pyinstaller \
		--windowed \
		--name=lidske-aktivity \
		--specpath=install \
		lidske_aktivity/__main__.py

dist-onefile:  ## Build one file distribution package
	docker run --rm --volume "$$(pwd):/app" lidske_aktivity \
	pipenv run pyinstaller \
		--onefile \
		--windowed \
		--name=lidske-aktivity \
		--specpath=install \
		lidske_aktivity/__main__.py

${_arch_linux_src_path}:
	git archive "v${_version}" --prefix "${_name}-${_version}/" \
		-o "${_arch_linux_src_path}"

${_arch_linux_pkg_path}: ${_arch_linux_src_path}
	cd "$$(dirname "${_arch_linux_src_path}")" && makepkg -f

dist-arch-linux: ${_arch_linux_pkg_path}  ## Build an Arch Linux package

install-arch-linux: ${_arch_linux_pkg_path}   ## Install built Arch Linux package
	sudo pacman -U "${_arch_linux_pkg_path}"

data/lidske-aktivity.svg:
	cd data && ./draw_svg_icon.py > lidske-aktivity.svg

data/lidske-aktivity.png: data/lidske-aktivity.svg
	cd data && rsvg-convert -w 48 -h 48 \
		lidske-aktivity.svg > lidske-aktivity.png

build: data/lidske-aktivity.png  ## Build the app using setuptools
	python setup.py build

clean:  ## Clean distribution package
	-rm install/arch_linux/*.tar.xz
	-rm data/*.png
	-rm data/*.svg
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

lint-arch-linux:
	namcap install/arch_linux/PKGBUILD

check:  ## Test installed app
	pytest lidske_aktivity/tests

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'
