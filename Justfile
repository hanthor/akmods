# Justfile for local development and CI mimicry

# Default values for build arguments
FEDORA_MAJOR_VERSION ?= "42"
KERNEL_FLAVOR ?= "main"
ARCH ?= "x86_64"

# Function to get kmods from kmods.yaml based on cfile_suffix and conditions
_get_kmods = '''
#!/bin/bash

KMOD_TYPE="$1"
FEDORA_MAJOR_VERSION="$2"
KERNEL_FLAVOR="$3"

yq eval ".kmods.${KMOD_TYPE}[] | select(true"

# Add conditional logic based on kmods.yaml
# This is a simplified example, full implementation would be more complex
# and involve iterating through conditions in YAML

# Example for 'evdi' kmod
if [ "${KMOD_TYPE}" == "extra" ] && [ "${FEDORA_MAJOR_VERSION}" -ge 42 ] && [[ ! "${KERNEL_FLAVOR}" =~ "asus" ]]; then
    yq eval ".kmods.extra[] | select(.name == \"evdi\") | .name" kmods.yaml
fi

# Example for 'facetimehd', 'rtl8814au', 'rtl88xxau', 'VirtualBox'
if [ "${KMOD_TYPE}" == "extra" ] && [[ ! "${KERNEL_FLAVOR}" =~ "bazzite" ]]; then
    yq eval ".kmods.extra[] | select(.name == \"facetimehd\" or .name == \"rtl8814au\" or .name == \"rtl88xxau\" or .name == \"VirtualBox\") | .name" kmods.yaml
fi

# Example for 'gpd-fan'
if [ "${KMOD_TYPE}" == "extra" ] && [ "${FEDORA_MAJOR_VERSION}" -ge 41 ]; then
    yq eval ".kmods.extra[] | select(.name == \"gpd-fan\") | .name" kmods.yaml
fi

# This is a placeholder. A robust solution would involve parsing all conditions from kmods.yaml
# and dynamically building the yq query.

# For now, we'll just list all kmods for the given type
yq eval ".kmods.${KMOD_TYPE}[].name" kmods.yaml | tr '\n' ' '
'''

# Base build command
_build_base = '''
    podman build \
        --build-arg FEDORA_MAJOR_VERSION={{FEDORA_MAJOR_VERSION}} \
        --build-arg KERNEL_FLAVOR={{KERNEL_FLAVOR}} \
        --build-arg ARCH={{ARCH}} \
        --build-arg DUAL_SIGN=true \
'''

# Recipe to build common akmods
common:
    @echo "Building common akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    KMODS_TO_BUILD := $(shell ./build_files/shared/get_kmods_to_build.sh common {{FEDORA_MAJOR_VERSION}} {{KERNEL_FLAVOR}})
    {{_build_base}} \
        --build-arg KMODS_TO_BUILD="$(echo "{{KMODS_TO_BUILD}}" | tr -d '\n')" \
        -f Containerfile.common .

# Recipe to build extra akmods
extra:
    @echo "Building extra akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    KMODS_TO_BUILD := $(shell ./build_files/shared/get_kmods_to_build.sh extra {{FEDORA_MAJOR_VERSION}} {{KERNEL_FLAVOR}})
    {{_build_base}} \
        --build-arg KMODS_TO_BUILD="$(echo "{{KMODS_TO_BUILD}}" | tr -d '\n')" \
        -f Containerfile.extra .

# Recipe to build nvidia akmods (no KMODS_TO_BUILD arg needed for this one)
nvidia:
    @echo "Building nvidia akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    {{_build_base}} \
        -f Containerfile.nvidia .

# Recipe to build nvidia-open akmods (no KMODS_TO_BUILD arg needed for this one)
nvidia-open:
    @echo "Building nvidia-open akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    {{_build_base}} \
        -f Containerfile.nvidia-open .

# Recipe to build zfs akmods (no KMODS_TO_BUILD arg needed for this one)
zfs:
    @echo "Building zfs akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    {{_build_base}} \
        -f Containerfile.zfs .

# Default recipe (lists available recipes)
default:
    @just --list