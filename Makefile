# Get information from the system
NAME=$(shell grep "^name:" metadata.yaml | cut -d ":" -f 2 | sed "s/ //g")
BUILD_ON_NAME=$(shell grep "name" charmcraft.yaml | head -n 1 | cut -d ":" -f 2 | sed "s/ //g")
BUILD_ON_CHANNEL=$(shell grep "channel" charmcraft.yaml | head -n 1 | cut -d ":" -f 2 | sed "s/ //g")
ARCH=$(shell dpkg-architecture -q DEB_BUILD_ARCH)

# Compose internal variables
CHARMNAME=$(NAME)_$(BUILD_ON_NAME)-$(BUILD_ON_CHANNEL)-$(ARCH).charm
removing ?= 1

clean:
	-juju remove-application $(NAME)

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
