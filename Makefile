_name=lidske-aktivity
_version=0.1.3
_pkgrel=1
_arch_linux_dist_parent=dist/arch_linux
_arch_linux_src_filename=${_name}-${_version}.tar.xz
_arch_linux_src_dirname=${_name}-${_version}
_arch_linux_pkg_filename=${_name}-${_version}-${_pkgrel}-any.pkg.tar.xz
_debian_dist_parent=dist/debian
_debian_src_filename=${_name}_${_version}.orig.tar.xz
_debian_src_dirname=${_name}-${_version}
_debian_pkg_filename=${_name}_${_version}-${_pkgrel}_all.deb

.PHONY: build install run run-debug dist-pyinstaller-build dist-pyinstaller dist-pyinstaller-docker-build dist-pyinstaller-docker dist-arch-linux dist-debian-build dist-debian-shell dist-debian install-arch-linux install-debian generate-data clean clean-cache test lint lint-arch-linux lint-data check bump-version help

build:  ## Build the app using setuptools
	python3 setup.py build

install:  ## Install built files to the filesystem
ifeq (,$(DESTDIR))
	@echo "You must set the variable 'DESTDIR'."
	@exit 1
endif
	python3 setup.py install --root="${DESTDIR}/" --optimize=1 --skip-build

run:  ## Start the app
	pipenv run python3 -m lidske_aktivity

run-debug:  ## Start the app with extended logging
	pipenv run python3 -m lidske_aktivity --verbose

dist-pyinstaller-build:
	pipenv --three --site-packages
	pipenv install --dev

dist-pyinstaller:  ## Build a PyInstaller-based package (with Docker)
	pipenv run pyinstaller \
		--onefile \
		--windowed \
		--name=lidske-aktivity \
		--specpath=pyinstaller \
		lidske_aktivity/__main__.py

dist-pyinstaller-docker-build:
	docker build -f docker/pyinstaller/Dockerfile -t lidske_aktivity_pyinstaller .

dist-pyinstaller-docker: | dist-pyinstaller-build  ## Build a PyInstaller-based package (without Docker)
	docker run --rm --volume "$$(pwd):/app" -e PYTHONHASHSEED=1 \
		lidske_aktivity_pyinstaller \
		pipenv run pyinstaller \
			--onefile \
			--windowed \
			--name=lidske-aktivity \
			--specpath=pyinstaller \
			lidske_aktivity/__main__.py

${_arch_linux_dist_parent}/${_arch_linux_src_filename}:
	mkdir -p "${_arch_linux_dist_parent}"
	git archive "v${_version}" --prefix "${_arch_linux_src_dirname}/" \
		-o "${_arch_linux_dist_parent}/${_arch_linux_src_filename}"

${_arch_linux_dist_parent}/PKGBUILD: ${_arch_linux_dist_parent}/${_arch_linux_src_filename}
	mkdir -p "${_arch_linux_dist_parent}"
	cp arch_linux/PKGBUILD "${_arch_linux_dist_parent}"
	cd "${_arch_linux_dist_parent}" && makepkg -g >> PKGBUILD
	cp -f "${_arch_linux_dist_parent}/PKGBUILD" arch_linux/PKGBUILD

${_arch_linux_dist_parent}/${_arch_linux_pkg_filename}: ${_arch_linux_dist_parent}/PKGBUILD
	cd "${_arch_linux_dist_parent}" && makepkg -f

dist-arch-linux: ${_arch_linux_dist_parent}/${_arch_linux_pkg_filename}  ## Build an Arch Linux package

install-arch-linux: ${_arch_linux_pkg_path}   ## Install built Arch Linux package
	sudo pacman -U "${_arch_linux_pkg_path}"

dist-debian-build:
	docker build -f docker/debian/Dockerfile -t lidske_aktivity_debian .

dist-debian-shell:
	docker run -it --volume="$$(pwd)/${_debian_dist_parent}:/app" lidske_aktivity_debian \
		bash

${_debian_dist_parent}/${_debian_src_filename}:
	mkdir -p "${_debian_dist_parent}"
	tar cJvf "${_debian_dist_parent}/${_debian_src_filename}" \
		-X .tarignore \
		--transform 's,^\.,${_debian_src_dirname},' .

${_debian_dist_parent}/${_debian_src_dirname}: ${_debian_dist_parent}/${_debian_src_filename}
	cd "${_debian_dist_parent}" && tar xvf "${_debian_src_filename}"

${_debian_dist_parent}/${_debian_pkg_filename}: ${_debian_dist_parent}/${_debian_src_dirname} | dist-debian-build
	docker run --rm --volume="$$(pwd)/${_debian_dist_parent}:/app" lidske_aktivity_debian \
		sh -c 'cd "${_debian_src_dirname}" && debuild -us -uc'

dist-debian: ${_debian_dist_parent}/${_debian_pkg_filename}  ## Build a Debian package

install-debian: ${_debian_dist_parent}/${_debian_pkg_filename}   ## Install built Debian package
	sudo dpkg -i "${_debian_dist_parent}/${_debian_pkg_filename}"
	sudo apt-get install -f --yes

data/lidske-aktivity.svg:
	cd data && python3 draw_svg_icon.py > lidske-aktivity.svg

data/lidske-aktivity.png: data/lidske-aktivity.svg
	cd data && rsvg-convert -w 48 -h 48 \
		lidske-aktivity.svg > lidske-aktivity.png

generate-data: data/lidske-aktivity.png

clean:  ## Clean distribution package
	-rm -rf build
	-rm -rf dist

clean-cache:  ## Clean cache
	pipenv run python3 -m lidske_aktivity --verbose --clean

test:  ## Run unit tests
	tox -e py37

lint:  ## Run linting
	tox -e lint

lint-arch-linux:
	namcap install/arch_linux/PKGBUILD

lint-data:
	desktop-file-validate data/lidske-aktivity.desktop

check:  ## Test installed app
	python3 -m pytest lidske_aktivity/tests

bump-version:
ifeq (,$(version))
	@echo "You must set the variable 'version'."
	@exit 1
endif
	sed -E -i s/${_version}/${version}/ Makefile
	sed -E -i s/${_version}/${version}/ lidske_aktivity/__init__.py
	sed -E -i s/${_version}/${version}/ arch_linux/PKGBUILD
	docker run -it --volume="$$(pwd):/app" \
		-e NAME="Jakub Valenta" -e EMAIL="jakub@jakubvalenta.cz" \
		lidske_aktivity_debian dch -v "${version}-${_pkgrel}" "New version"

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'
