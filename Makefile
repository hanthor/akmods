# Makefile for local development and CI mimicry

# Default values for build arguments
MAJOR_VERSION ?= 42
KERNEL_FLAVOR ?= main
ARCH ?= x86_64

PYTHON := ./.venv/bin/python3

.PHONY: venv kernel build-kmods list-build-matrix default help

# Recipe to build the kernel
kernel:
	@echo "Fetching and building kernel for Fedora $(MAJOR_VERSION) (Kernel: $(KERNEL_FLAVOR), Arch: $(ARCH))"
	podman pull quay.io/fedora/fedora:$(MAJOR_VERSION)
	mkdir -p /tmp/kernel-cache
	install -m 755 fetch-kernel.sh /tmp/kernel-cache/fetch-kernel.sh
	cp -a certs /tmp/kernel-cache
	podman run --user root \
		--entrypoint /bin/bash \
		--env MAJOR_VERSION=$(MAJOR_VERSION) \
		--env KERNEL_FLAVOR=$(KERNEL_FLAVOR) \
		--env KERNEL_VERSION=6.8.9-200.fc39.x86_64 \
		--env KERNEL_BUILD_TAG=f39 \
		--env DUAL_SIGN=true \
		-v /tmp/kernel-cache:/tmp/kernel-cache:rw,z \
		quay.io/fedora/fedora:$(MAJOR_VERSION) \
		-c "chmod +x /tmp/kernel-cache/fetch-kernel.sh && /tmp/kernel-cache/fetch-kernel.sh /tmp/kernel-cache"

# Generic recipe to build akmods based on KMOD_TYPE and IMAGE_NAME
build-kmods: kernel
	@echo "Building $(KMOD_TYPE) akmods for image $(IMAGE_NAME) on Fedora $(MAJOR_VERSION) (Kernel: $(KERNEL_FLAVOR), Arch: $(ARCH))"
	$(eval KMOD_VARS := $(shell PATH=./.venv/bin:$PATH ./.venv/bin/python3 ./build_files/shared/get_kmods_to_build.py $(KMOD_TYPE) $(MAJOR_VERSION) $(KERNEL_FLAVOR) $(IMAGE_NAME)))
	$(foreach VAR,$(KMOD_VARS),$(eval $(VAR)))
	
	$(eval CPP_DEFINES := $(shell PATH=./.venv/bin:$PATH ./.venv/bin/python3 ./build_files/shared/generate_cpp_defines.py build_configurations.yaml))
	cat Containerfile.in | \
		sed "s|# KMOD_COPR_REPOS_ADD_INSTRUCTIONS|$(COPR_REPOS_ADD_INSTRUCTIONS)|g" | \
		sed "s|# KMOD_INSTALL_AND_BUILD_COMMANDS|$(DNF_INSTALL_COMMANDS)$(AKMODS_FORCE_COMMANDS)|g" | \
		cpp -P - \
		podman build \
		--build-arg MAJOR_VERSION=$(MAJOR_VERSION) \
		--build-arg KERNEL_FLAVOR=$(KERNEL_FLAVOR) \
		--build-arg ARCH=$(ARCH) \
		--build-arg DUAL_SIGN=true \
		--build-arg KMODS_TO_BUILD="$(KMODS_TO_BUILD)" \
		-f - .

# Default recipe (lists available recipes)
default: help

venv:
	@echo "Setting up Python virtual environment..."
	@uv venv

list-build-matrix: venv
	@echo "Listing potential images from build_configurations.yaml:"
	@$(PYTHON) ./build_files/shared/list_images.py build_configurations.yaml

help:
	@echo "Available recipes:"
	@echo "  kernel                                 ## Fetches and builds the kernel"
	@echo "  build-kmods KMOD_TYPE=<type> IMAGE_NAME=<name> ## Builds akmods for a specific type (e.g., common, extra, nvidia, zfs) and image (e.g., cayo-base-main-10)"
	@echo "  list-build-matrix                      ## Lists potential images based on build_configurations.yaml"
	@echo "  help                                   ## Displays this help message"

