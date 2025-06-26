# Justfile for local development and CI mimicry

# Default values for build arguments
FEDORA_MAJOR_VERSION ?= "42"
KERNEL_FLAVOR ?= "main"
ARCH ?= "x86_64"

# Define common kmods
COMMON_KMODS = "framework-laptop kvmfr openrazer v4l2loopback wl xone"

# Define extra kmods with conditional logic (mimicking reusable-build.yml)
# This is a simplified version for local testing; full CI logic is more complex
EXTRA_KMODS = "ayaneo-platform ayn-platform bmi260 gcadapter_oc gpd-fan nct6687d ryzen-smu system76 system76-io vhba VirtualBox evdi facetimehd rtl8814au rtl88xxau zenergy"

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
    {{_build_base}} \
        --build-arg KMODS_TO_BUILD="{{COMMON_KMODS}}" \
        -f Containerfile.common .

# Recipe to build extra akmods
extra:
    @echo "Building extra akmods for Fedora {{FEDORA_MAJOR_VERSION}} (Kernel: {{KERNEL_FLAVOR}}, Arch: {{ARCH}})"
    {{_build_base}} \
        --build-arg KMODS_TO_BUILD="{{EXTRA_KMODS}}" \
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
