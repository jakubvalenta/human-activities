_name=lidske-aktivity
_version=0.1.1
_arch_linux_pkgrel=1
_arch_linux_dist_parent=dist/arch_linux
_arch_linux_src_filename=${_name}-${_version}.tar.xz
_arch_linux_src_dirname=${_name}-${_version}
_arch_linux_pkg_filename=${_name}-${_version}-${_arch_linux_pkgrel}-any.pkg.tar.xz

.PHONY: run run-debug dist-prepare dist dist-onefile dist-arch-linux install-arch-linux build build-data clean clean-cache test unit-test lint lint-arch-linux check help

build: data/lidske-aktivity.png  ## Build the app using setuptools
	python3 setup.py build

install:  ## Install built files to the filesystem
ifeq (,$(DESTDIR))
	@echo "You must set the variable `DESTDIR`."
	@exit 1
endif
	install -D data/lidske-aktivity.desktop "$DESTDIR/usr/share/applications/"
	install -D data/lidske-aktivity.desktop "$DESTDIR/etc/xdg/autostart/"
	install -D data/lidske-aktivity.png "$DESTDIR/usr/share/pixmaps/"
	install -D data/lidske-aktivity.svg "$DESTDIR/usr/share/icons/hicolor/scalable/apps/"
	python3 setup.py install --root="$DESTDIR/" --optimize=1 --skip-build

run:  ## Start the app
	pipenv run python3 -m lidske_aktivity

run-debug:  ## Start the app with extended logging
	pipenv run python3 -m lidske_aktivity --verbose

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

${_arch_linux_dist_parent}/${_arch_linux_src_filename}:
	mkdir -p "${_arch_linux_dist_parent}"
	git archive "v${_version}" --prefix "${_arch_linux_src_dirname}/" \
		-o "${_arch_linux_dist_parent}/${_arch_linux_src_filename}"

${_arch_linux_dist_parent}/PKGBUILD:
	mkdir -p "${_arch_linux_dist_parent}"
	cp arch_linux/PKGBUILD "${_arch_linux_dist_parent}"

${_arch_linux_dist_parent}/${_arch_linux_pkg_filename}: ${_arch_linux_dist_parent}/${_arch_linux_src_filename} ${_arch_linux_dist_parent}/PKGBUILD
	cd "${_arch_linux_dist_parent}" && makepkg -f

dist-arch-linux: ${_arch_linux_dist_parent}/${_arch_linux_pkg_filename}  ## Build an Arch Linux package

install-arch-linux: ${_arch_linux_pkg_path}   ## Install built Arch Linux package
	sudo pacman -U "${_arch_linux_pkg_path}"

data/lidske-aktivity.svg:
	cd data && python3 draw_svg_icon.py > lidske-aktivity.svg

data/lidske-aktivity.png: data/lidske-aktivity.svg
	cd data && rsvg-convert -w 48 -h 48 \
		lidske-aktivity.svg > lidske-aktivity.png

clean:  ## Clean distribution package
	-rm -rf build
	-rm -rf dist

clean-cache:  ## Clean cache
	pipenv run python3 -m lidske_aktivity --verbose --clean

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
