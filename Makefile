_name=human-activities
_pypkgname=human_activities
_version=1.0.0
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

.PHONY: build
build:  ## Build the app using setuptools
	python3 setup.py build

.PHONY: install
install:  ## Install built files to the filesystem
ifeq (,$(DESTDIR))
	@echo "You must set the variable 'DESTDIR'."
	@exit 1
endif
	python3 setup.py install --root="${DESTDIR}/" --optimize=1 --skip-build

.PHONY: setup
setup:  ## Create Pipenv virtual environment and install dependencies.
	pipenv --three --site-packages
	pipenv install --dev

.PHONY: run
run:  ## Start the app
	pipenv run python3 -m ${_pypkgname}

.PHONY: run-debug
run-debug:  ## Start the app with extended logging
	pipenv run python3 -m ${_pypkgname} --verbose

.PHONY: run-wx
run-wx:  ## Start the app with the WxWidgets backend and extended logging
	pipenv run python3 -m ${_pypkgname} --verbose --backend=wx

.PHONY: run-qt
run-qt:  ## Start the app with the Qt backend and extended logging
	pipenv run python3 -m ${_pypkgname} --verbose --backend=qt

${_arch_linux_dist_parent}/${_arch_linux_src_filename}:
	mkdir -p "${_arch_linux_dist_parent}"
	tar cJvf "${_arch_linux_dist_parent}/${_arch_linux_src_filename}" \
		-X .tarignore \
		--transform 's,^\.,${_arch_linux_src_dirname},' .

${_arch_linux_dist_parent}/PKGBUILD: ${_arch_linux_dist_parent}/${_arch_linux_src_filename}
	mkdir -p "${_arch_linux_dist_parent}"
	cp arch_linux/PKGBUILD "${_arch_linux_dist_parent}"
	cd "${_arch_linux_dist_parent}" && makepkg -g >> PKGBUILD
	cp -f "${_arch_linux_dist_parent}/PKGBUILD" arch_linux/PKGBUILD

${_arch_linux_dist_parent}/${_arch_linux_pkg_filename}: ${_arch_linux_dist_parent}/PKGBUILD
	cd "${_arch_linux_dist_parent}" && makepkg -sf

dist-arch-linux: ${_arch_linux_dist_parent}/${_arch_linux_pkg_filename}  ## Build an Arch Linux package

.PHONY: install-arch-linux
install-arch-linux: ${_arch_linux_dist_parent}/${_arch_linux_pkg_filename}  ## Install built Arch Linux package
	sudo pacman -U "$<"

.PHONY: dist-debian-build
dist-debian-build:
	docker build -f debian/Dockerfile -t human_activities_debian .

.PHONY: dist-debian-shell
dist-debian-shell:
	docker run --rm -it -u "${_uid}:${_gid}" -v "$$(pwd):/app" \
		human_activities_debian \
		bash

.PHONY: dist-mac
dist-mac:  ## Build macOS package
	-rm -r build/human-activities
	-rm -r dist/human-activities
	-rm -r "dist/Human Activities.app"
	-rm -r dist/Human_Activities*.zip
	sh mac/pyinstaller.sh
	cd dist && zip -r "Human_Activities-${_version}.zip" "Human Activities.app"

${_debian_dist_parent}/${_debian_src_filename}:
	mkdir -p "${_debian_dist_parent}"
	tar cJvf "${_debian_dist_parent}/${_debian_src_filename}" \
		-X .tarignore \
		--transform 's,^\.,${_debian_src_dirname},' .

${_debian_dist_parent}/${_debian_src_dirname}: ${_debian_dist_parent}/${_debian_src_filename}
	cd "${_debian_dist_parent}" && tar xvf "${_debian_src_filename}"

${_debian_dist_parent}/${_debian_pkg_filename}: ${_debian_dist_parent}/${_debian_src_dirname}
	docker run --rm \
		-u "${_uid}:${_gid}" \
		-v "$$(pwd):/app" \
		-w "/app/${_debian_dist_parent}/${_debian_src_dirname}" \
		human_activities_debian \
		debuild -us -uc

dist-debian: ${_debian_dist_parent}/${_debian_pkg_filename}  ## Build a Debian package

.PHONY: dist-debian-sign
dist-debian-sign: ${_debian_dist_parent}/${_debian_pkg_filename}  ## Sign the Debian package
ifeq ($(key_id),)
	@echo "You must define the variable 'key_id'"
	exit 1
endif
	 # See https://nixaid.com/using-gpg-inside-a-docker-container/
	docker run --rm -it -u "${_uid}:${_gid}" -v "$$(pwd):/app" \
		-v "${HOME}/.gnupg/:/.gnupg/:ro" \
		--tmpfs "/run/user/${_uid}/:mode=0700,uid=${_uid},gid=${_gid}" \
		-w "/app/${_debian_dist_parent}" \
		human_activities_debian \
		sh -c 'gpg-agent --daemon && dpkg-sig -k "${key_id}" --sign builder "${_debian_pkg_filename}"'

.PHONY: dist-debian-verify
dist-debian-verify: ${_debian_dist_parent}/${_debian_pkg_filename} | dist-debian-build  ## Verify the signature of the Debian package
	 # See https://nixaid.com/using-gpg-inside-a-docker-container/
	docker run --rm -it -u "${_uid}:${_gid}" -v "$$(pwd):/app:ro" \
		-v "${HOME}/.gnupg/:/.gnupg/:ro" \
		--tmpfs "/run/user/${_uid}/:mode=0700,uid=${_uid},gid=${_gid}" \
		-w "/app/${_debian_dist_parent}" \
		human_activities_debian \
		sh -c 'gpg-agent --daemon && dpkg-sig --verify "${_debian_pkg_filename}"'

.PHONY: install-debian
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

.PHONY: generate-data
generate-data: data/${_name}.png

.PHONY: clean-cache
clean-cache:  ## Clean cache
	pipenv run python3 -m ${_pypkgname} --verbose --clean

.PHONY: test
test:  ## Run unit tests
	tox -e py39

.PHONY: lint
lint:  ## Run linting
	tox -e lint

.PHONY: lint-arch-linux
lint-arch-linux:
	namcap install/arch_linux/PKGBUILD

.PHONY: lint-data
lint-data:
	desktop-file-validate "data/${_name}.desktop"

.PHONY: reformat
reformat:  ## Reformat Python code using Black
	black -l 79 --skip-string-normalization ${_pypkgname}

.PHONY: check
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

.PHONY: clean-lang
clean-lang:  ## Clean gettext .pot and .mo files
	-rm lang/${_name}.pot
	-rm ${_pypkgname}/locale/*/LC_MESSAGES/${_name}.mo

.PHONY: gen-lang
gen-lang: | ${_pypkgname}/locale/en_US/LC_MESSAGES/${_name}.mo ${_pypkgname}/locale/cs_CZ/LC_MESSAGES/${_name}.mo  ## Generate gettext .pot and .mo files

.PHONY: bump-version
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
	docker run --rm -it -u "${_uid}:${_gid}" -v "$$(pwd):/app" \
		-e NAME="Jakub Valenta" -e EMAIL="jakub@jakubvalenta.cz" \
		human_activities_debian \
		dch -v "${version}-${_pkgrel}" "New version"
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

.PHONY: backup
backup:  ## Backup built packages
	mkdir -p "bak/${_timestamp}"
	-cp -a "${_debian_dist_parent}/"*.deb "bak/${_timestamp}"
	-cp -a "${_arch_linux_dist_parent}/"*.pkg.tar.xz "bak/${_timestamp}"
	-cp -a dist/*.app "bak/${_timestamp}"
	-cp -a dist/*.exe "bak/${_timestamp}"

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'
