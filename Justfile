# Justfile for local development and CI mimicry

# Default values for build arguments
FEDORA_MAJOR_VERSION ?= "42"
KERNEL_FLAVOR ?= "main"
ARCH ?= "x86_64"

# Base build command
_build_base = '''
    podman build \
        --build-arg FEDORA_MAJOR_VERSION={{FEDORA_MAJOR_VERSION}} \
        --build-arg KERNEL_FLAVOR={{KERNEL_FLAVOR}} \
        --build-arg ARCH={{ARCH}} \
        --build-arg DUAL_SIGN=true \
'''

# Recipe to build the kernel
kernel:
    @echo "Fetching and building kernel for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    podman pull quay.io/fedora/fedora:{{FEDORA_MAJOR_VERSION}}
    mkdir -p /tmp/kernel-cache
    cp -a fetch-kernel.sh certs /tmp/kernel-cache
    podman run \
        --entrypoint /bin/bash \
        --env FEDORA_VERSION={{FEDORA_MAJOR_VERSION}} \
        --env KERNEL_FLAVOR={{KERNEL_FLAVOR}} \
        --env DUAL_SIGN=true \
        -v /tmp/kernel-cache:/tmp/kernel-cache:rw \
        quay.io/fedora/fedora:{{FEDORA_MAJOR_VERSION}} \
        /tmp/kernel-cache/fetch-kernel.sh /tmp/kernel-cache

# Recipe to build common akmods
common: kernel
    @echo "Building common akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    KMODS_TO_BUILD := $(shell ./build_files/shared/get_kmods_to_build.sh common {{FEDORA_MAJOR_VERSION}} {{KERNEL_FLAVOR}})
    {{_build_base}} \
        --build-arg KMODS_TO_BUILD="{{KMODS_TO_BUILD}}" \
        -f Containerfile.common .

# Recipe to build extra akmods
extra: kernel
    @echo "Building extra akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    KMODS_TO_BUILD := $(shell ./build_files/shared/get_kmods_to_build.sh extra {{FEDORA_MAJOR_VERSION}} {{KERNEL_FLAVOR}})
    {{_build_base}} \
        --build-arg KMODS_TO_BUILD="{{KMODS_TO_BUILD}}" \
        -f Containerfile.extra .

# Recipe to build nvidia akmods (no KMODS_TO_BUILD arg needed for this one)
nvidia: kernel
    @echo "Building nvidia akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    {{_build_base}} \
        -f Containerfile.nvidia .

# Recipe to build nvidia-open akmods (no KMODS_TO_BUILD arg needed for this one)
nvidia-open: kernel
    @echo "Building nvidia-open akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    {{_build_base}} \
        -f Containerfile.nvidia-open .

# Recipe to build zfs akmods (no KMODS_TO_BUILD arg needed for this one)
zfs: kernel
    @echo "Building zfs akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    {{_build_base}} \
        -f Containerfile.zfs .

# Default recipe (lists available recipes)
default:
    @just --list
