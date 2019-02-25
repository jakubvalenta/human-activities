_name=human-activities
_pypkgname=human_activities
_version=0.9.0
_pkgrel=1
_arch_linux_dist_parent=dist/arch_linux
_arch_linux_src_filename=${_name}-${_version}.tar.xz
_arch_linux_src_dirname=${_name}-${_version}
_arch_linux_pkg_filename=${_name}-${_version}-${_pkgrel}-any.pkg.tar.xz
_debian_dist_parent=dist/debian
_debian_src_filename=${_name}_${_version}.orig.tar.xz
_debian_src_dirname=${_name}-${_version}
_debian_pkg_filename=${_name}_${_version}-${_pkgrel}_all.deb
_uid=$(shell id -u)
_gid=$(shell id -g)
_timestamp=$(shell date +%s)

.PHONY: build install setup setup-dev run run-debug run-wx run-qt dist-arch-linux dist-debian-build dist-debian-shell dist-debian install-arch-linux install-debian generate-data clean-cache test lint lint-arch-linux lint-data reformat check clean-lang gen-lang bump-version backup help

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

run-qt:  ## Start the app with the Qt backend and extended logging
	pipenv run python3 -m ${_pypkgname} --verbose --qt

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

dist-arch-linux:  ## Build an Arch Linux package
	-rm -r dist/arch_linux
	$(MAKE) ${_arch_linux_dist_parent}/${_arch_linux_pkg_filename}

install-arch-linux: ${_arch_linux_pkg_path}   ## Install built Arch Linux package
	sudo pacman -U "${_arch_linux_pkg_path}"

dist-debian-build:
	docker build -f debian/Dockerfile -t human_activities_debian .

dist-debian-shell:
	docker run -it --volume="$$(pwd)/${_debian_dist_parent}:/app" human_activities_debian \
		bash

${_debian_dist_parent}/${_debian_src_filename}:
	mkdir -p "${_debian_dist_parent}"
	tar cJvf "${_debian_dist_parent}/${_debian_src_filename}" \
		-X .tarignore \
		--transform 's,^\.,${_debian_src_dirname},' .

${_debian_dist_parent}/${_debian_src_dirname}: ${_debian_dist_parent}/${_debian_src_filename}
	cd "${_debian_dist_parent}" && tar xvf "${_debian_src_filename}"

${_debian_dist_parent}/${_debian_pkg_filename}: ${_debian_dist_parent}/${_debian_src_dirname} | dist-debian-build
	docker run --rm --volume="$$(pwd)/${_debian_dist_parent}:/app" human_activities_debian \
		sh -c 'cd "${_debian_src_dirname}" && debuild -us -uc; chown -R ${_uid}:${_gid} /app'

dist-debian:  ## Build a Debian package
	-rm -r dist/debian
	$(MAKE) ${_debian_dist_parent}/${_debian_pkg_filename}

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

clean-cache:  ## Clean cache
	pipenv run python3 -m ${_pypkgname} --verbose --clean

test:  ## Run unit tests
	tox -e py37

lint:  ## Run linting
	tox -e lint

lint-arch-linux:
	namcap install/arch_linux/PKGBUILD

lint-data:
	desktop-file-validate "data/${_name}.desktop"

reformat:  ## Reformat Python code using Black
	black -l 79 --skip-string-normalization ${_pypkgname}

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

clean-lang:  ## Clean gettext .pot and .mo files
	-rm lang/${_name}.pot
	-rm ${_pypkgname}/locale/*/LC_MESSAGES/${_name}.mo

gen-lang: | ${_pypkgname}/locale/en_US/LC_MESSAGES/${_name}.mo ${_pypkgname}/locale/cs_CZ/LC_MESSAGES/${_name}.mo  ## Generate gettext .pot and .mo files

bump-version:  ## Increase application version (automatically change code)
ifeq (,$(version))
	@echo "You must set the variable 'version'."
	@exit 1
endif
	sed -i s/${_version}/${version}/g Makefile
	sed -i s/${_version}/${version}/g README.rst
	sed -i s/${_version}/${version}/g ${_pypkgname}/__init__.py
	sed -i s/${_version}/${version}/g arch_linux/PKGBUILD
	docker info &> /dev/null || sudo systemctl start docker
	docker run -it --volume="$$(pwd):/app" \
		-e NAME="Jakub Valenta" -e EMAIL="jakub@jakubvalenta.cz" \
		human_activities_debian dch -v "${version}-${_pkgrel}" "New version"
	@echo "Editing changelog..."
	"${EDITOR}" debian/changelog
	@echo "Committing changes..."
	git add \
		Makefile \
		README.rst \
		${_pypkgname}/__init__.py \
		arch_linux/PKGBUILD debian/changelog
	git commit -m "Version ${version}"
	@echo "Creating tag..."
	git tag "v${version}"
	@echo "Done"

backup:  ## Backup built packages
	mkdir -p "bak/${_timestamp}"
	cp "${_debian_dist_parent}/${_debian_pkg_filename}" "bak/${_timestamp}"
	cp "${_arch_linux_dist_parent}/${_arch_linux_pkg_filename}" "bak/${_timestamp}"
	cp -a "${_arch_linux_dist_parent}/*.app" "bak/${_timestamp}"

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'
