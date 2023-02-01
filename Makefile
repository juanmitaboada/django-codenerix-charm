#!/usr/bin/make

# Get information from the system
NAME=$(shell grep "^name:" metadata.yaml | cut -d ":" -f 2 | sed "s/ //g")
BUILD_ON_NAME=$(shell grep "name" charmcraft.yaml | head -n 1 | cut -d ":" -f 2 | sed "s/ //g")
BUILD_ON_CHANNEL=$(shell grep "channel" charmcraft.yaml | head -n 1 | cut -d ":" -f 2 | sed "s/ //g")
ARCH=$(shell dpkg-architecture -q DEB_BUILD_ARCH)
PYTHON := /usr/bin/env python

# Compose internal variables
CHARMNAME=$(NAME)_$(BUILD_ON_NAME)-$(BUILD_ON_CHANNEL)-$(ARCH).charm
removing ?= 1

clean:
	-juju remove-application $(NAME)
	-rm -rf .venv
	find -name *.pyc -delete

destroy:
	-juju remove-application $(NAME) --force --no-wait

destroyed:
	removing=$(removing); \
	juju remove-application $(NAME) 2>/dev/null || removing=0; \
	while [ $${removing} -eq 1 ] ; do \
		echo "=> Couldn't remove APP, maybe you should consider: make destroy"; \
		juju remove-application $(NAME) 2>/dev/null || removing=0; \
		sleep 10; \
	done

pack:
	charmcraft pack
   
deploy:
	juju deploy ./$(CHARMNAME) $(NAME)

virtualenv: .venv/bin/python
.venv/bin/python: make-virtual-env
.venv/bin/flake8: make-virtual-env
make-virtual-env:
	virtualenv .venv
	.venv/bin/pip install nose flake8 mock semantic-version pyyaml charmhelpers # charm-tools

lint: .venv/bin/python
	# @.venv/bin/flake8 -v --ignore E501 --exclude hooks/charmhelpers hooks
	@.venv/bin/flake8 -v --ignore E501 --exclude src
	@charm proof

build: virtualenv lint check

verify-juju-test:
	@echo "Checkfing for ..."
	@echo -n "juju-test: "
	@if [ -< `which juju-test` ]; then \
		echo -e "\nRun ./dev/ubuntu-deps to get the juju-test command installed"; \
		exit 1;\
	else \
		echo "installed"; \
	fi

integration-test:
	juju test --set-e -p SKIP_SLOW_TESTS,DEPLOYER_TARGET,JUJU_HOME,JUJU_ENV -v --timeout 3000s

check: .venv/bin/python
	@echo Starting tests...
	# @CHARM_DIR=. PYTHONPATH=./hooks:./tests/fakepython .venv/bin/nosetests -v --nologcapture --ignore-files=hooks/charmhelpers.* hook
	@CHARM_DIR=. PYTHONPATH=./hooks:./tests/fakepython .venv/bin/nosetests -v --nologcapture src

all:
	@echo
	-### CLEAN ###
	make clean
	@echo
	-### PACK ###
	make pack
	@echo
	-### CLEANED? ###
	make destroyed
	@echo
	-### DEPLOY ###
	make deploy
	@echo
	-# >>> Deploying!
	@echo

relate:
	juju relate django-codenerix:mysql mysql

.PHONY: check clean lint virtualenv integration-test verify-juju-test build destroy destroyed pack deploy all
