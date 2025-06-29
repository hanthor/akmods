#!/bin/sh

set -oeux pipefail

RELEASE="$(rpm -E '%fedora')"

if [[ "${RELEASE}" -ge 43 ]]; then
    COPR_RELEASE="rawhide"
else
    COPR_RELEASE="${RELEASE}"
fi

/tmp/build-kmod.sh vhba "https://copr.fedorainfracloud.org/coprs/rok/cdemu/repo/fedora-${COPR_RELEASE}/rok-cdemu-fedora-${COPR_RELEASE}.repo" "_copr_rok-cdemu.repo" vhba