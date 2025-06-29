#!/bin/sh

set -oeux pipefail

RELEASE="$(rpm -E '%fedora')"

/tmp/build-kmod.sh openrazer "https://copr.fedorainfracloud.org/coprs/ublue-os/akmods/repo/fedora-${RELEASE}/ublue-os-akmods-fedora-${RELEASE}.repo" "_copr_ublue-os-akmods.repo" razerkbd razermouse razerkraken razeraccessory