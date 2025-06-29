#!/bin/sh

set -oeux pipefail

RELEASE="$(rpm -E '%fedora')"

/tmp/build-kmod.sh nct6687d "https://copr.fedorainfracloud.org/coprs/ublue-os/akmods/repo/fedora-${RELEASE}/ublue-os-akmods-fedora-${RELEASE}.repo" "_copr_ublue-os-akmods.repo" nct6687