_name=lidske-aktivity
_pypkgname=lidske_aktivity
_version=0.4.0
_pkgrel=1
_arch_linux_dist_parent=dist/arch_linux
_arch_linux_src_filename=${_name}-${_version}.tar.xz
_arch_linux_src_dirname=${_name}-${_version}
_arch_linux_pkg_filename=${_name}-${_version}-${_pkgrel}-any.pkg.tar.xz
_debian_dist_parent=dist/debian
_debian_src_filename=${_name}_${_version}.orig.tar.xz
_debian_src_dirname=${_name}-${_version}
_debian_pkg_filename=${_name}_${_version}-${_pkgrel}_all.deb

.PHONY: build install setup setup-dev run run-debug run-wx dist-pyinstaller-build dist-pyinstaller dist-arch-linux dist-debian-build dist-debian-shell dist-debian install-arch-linux install-debian generate-data clean clean-cache scan test lint lint-arch-linux lint-data check clean-lang gen-lang bump-version backup help

build:  ## Build the app using setuptools
	python3 setup.py build

install:  ## Install built files to the filesystem
ifeq (,$(DESTDIR))
	@echo "You must set the variable 'DESTDIR'."
	@exit 1
endif
	python3 setup.py install --root="${DESTDIR}/" --optimize=1 --skip-build

setup:  ## Create Pipenv virtual environment and install dependencies.
	pipenv --three --site-packages
	pipenv install --dev

setup-dev:  ## Install development dependencies
	pipenv install --dev

run:  ## Start the app
	pipenv run python3 -m ${_pypkgname}

run-debug:  ## Start the app with extended logging
	pipenv run python3 -m ${_pypkgname} --verbose

run-wx:  ## Start the app with the WxWidgets backend and extended logging
	pipenv run python3 -m ${_pypkgname} --verbose --wxwidgets

dist-pyinstaller-build:
	docker build -f linux_pyinstaller/Dockerfile -t lidske_aktivity_pyinstaller .

dist-pyinstaller: | dist-pyinstaller-build  ## Build a PyInstaller-based package (with Docker)
	docker run --rm --volume "$$(pwd):/app" -e PYTHONHASHSEED=1 lidske_aktivity_pyinstaller \
		pipenv run pyinstaller "linux_pyinstaller/${_name}.spec"

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
	cd "${_arch_linux_dist_parent}" && makepkg -sf

dist-arch-linux: ${_arch_linux_dist_parent}/${_arch_linux_pkg_filename}  ## Build an Arch Linux package

install-arch-linux: ${_arch_linux_pkg_path}   ## Install built Arch Linux package
	sudo pacman -U "${_arch_linux_pkg_path}"

dist-debian-build:
	docker build -f debian/Dockerfile -t lidske_aktivity_debian .

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
	cp -f data/*.service data/*.timer "${_debian_dist_parent}/${_debian_src_dirname}/debian"

${_debian_dist_parent}/${_debian_pkg_filename}: ${_debian_dist_parent}/${_debian_src_dirname} | dist-debian-build
	docker run --rm --volume="$$(pwd)/${_debian_dist_parent}:/app" lidske_aktivity_debian \
		sh -c 'cd "${_debian_src_dirname}" && debuild -us -uc'

dist-debian: ${_debian_dist_parent}/${_debian_pkg_filename}  ## Build a Debian package

install-debian: ${_debian_dist_parent}/${_debian_pkg_filename}   ## Install built Debian package
	sudo dpkg -i "${_debian_dist_parent}/${_debian_pkg_filename}"
	sudo apt-get install -f --yes

data/${_name}.svg:
	pipenv run python3 -c 'from ${_pypkgname} import icon; icon.print_default_svg_icon()' > "data/${_name}.svg"

data/${_name}.png: data/${_name}.svg
	sh data/bin/create_png.sh

data/${_name}.ico: data/${_name}.png
	sh data/bin/create_ico.sh

data/${_name}.icns: data/${_name}.svg
	sh data/bin/create_icns.sh

generate-data: data/${_name}.png

clean:  ## Clean distribution package
	-rm -rf build/*
	-rm -rf dist/*

clean-cache:  ## Clean cache
	pipenv run python3 -m ${_pypkgname} --verbose --clean

scan:  ## Scan directories
	pipenv run python3 -m ${_pypkgname} --verbose --scan

test:  ## Run unit tests
	tox -e py37

lint:  ## Run linting
	tox -e lint

lint-arch-linux:
	namcap install/arch_linux/PKGBUILD

lint-data:
	desktop-file-validate "data/${_name}.desktop"
	systemd-analyze verify "data/${_name}.service"
	systemd-analyze verify "data/${_name}.timer"

check:  ## Test installed app
	python3 -m pytest ${_pypkgname}/tests

lang/${_name}.pot: $(wildcard ${_pypkgname}/*.py ${_pypkgname}/**/*.py)
	xgettext --language=Python --keyword=_ --output=$@ --from-code=UTF-8 \
		--package-name="${_name}" --package-version="${_version}" $^

lang/%.po: lang/${_name}.pot
	if [ -f $@ ]; then \
		msgmerge --update $@ $<; \
	else \
		msginit --output=$@ --input=$< --locale=en_US; \
	fi

${_pypkgname}/locale/%/LC_MESSAGES/${_name}.mo: lang/%.po
	mkdir -p "$$(dirname "$@")"
	msgfmt $< -o $@

clean-lang:
	-rm lang/${_name}.pot
	-rm ${_pypkgname}/locale/*/LC_MESSAGES/${_name}.mo

gen-lang: | ${_pypkgname}/locale/en_US/LC_MESSAGES/${_name}.mo ${_pypkgname}/locale/cs_CZ/LC_MESSAGES/${_name}.mo

bump-version:  ## Increase application version (automatically change code)
ifeq (,$(version))
	@echo "You must set the variable 'version'."
	@exit 1
endif
	sed -E -i s/${_version}/${version}/ Makefile
	sed -E -i s/${_version}/${version}/ ${_pypkgname}/__init__.py
	sed -E -i s/${_version}/${version}/ arch_linux/PKGBUILD
	docker run -it --volume="$$(pwd):/app" \
		-e NAME="Jakub Valenta" -e EMAIL="jakub@jakubvalenta.cz" \
		lidske_aktivity_debian dch -v "${version}-${_pkgrel}" "New version"
	@echo "Now commit the changes and run:"
	@echo "    git tag -a v${version}"

backup:  ## Backup built packages (currently Debian-only)
	timestamp=$$(date +%s) && \
	mkdir -p "bak/$$timestamp" && \
	cp "${_debian_dist_parent}/${_debian_pkg_filename}" "bak/$$timestamp"

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\0.4.0m %s\n", $$1, $$2}'


