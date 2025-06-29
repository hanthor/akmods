#!/bin/sh

set -oeux pipefail

/tmp/build-kmod.sh framework-laptop "https://copr.fedorainfracloud.org/coprs/ublue-os/akmods/repo/fedora-${RELEASE}/ublue-os-akmods-fedora-${RELEASE}.repo" "_copr_ublue-os-akmods.repo"