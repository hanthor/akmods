#!/bin/sh

set -oeux pipefail

RELEASE="$(rpm -E '%fedora')"

/tmp/build-kmod.sh bmi260 "https://copr.fedorainfracloud.org/coprs/ublue-os/akmods/repo/fedora-${RELEASE}/ublue-os-akmods-fedora-${RELEASE}.repo" "_copr_ublue-os-akmods.repo" bmi260_core bmi260_i2c