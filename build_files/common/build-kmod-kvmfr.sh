#!/bin/sh

set -oeux pipefail

RELEASE="$(rpm -E '%fedora')"

if [[ "${RELEASE}" -ge 41 ]]; then
    COPR_RELEASE="rawhide"
else
    COPR_RELEASE="${RELEASE}"
fi

/tmp/build-kmod.sh kvmfr "https://copr.fedorainfracloud.org/coprs/hikariknight/looking-glass-kvmfr/repo/fedora-${COPR_RELEASE}/hikariknight-looking-glass-kvmfr-fedora-${COPR_RELEASE}.repo" "_copr_hikariknight-looking-glass-kvmfr.repo"