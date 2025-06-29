#!/bin/sh

set -oeux pipefail

RELEASE="$(rpm -E '%fedora')"

if [[ "${RELEASE}" -ge 41 ]]; then
    COPR_RELEASE="rawhide"
else
    COPR_RELEASE="${RELEASE}"
fi

/tmp/build-kmod.sh system76-driver "https://copr.fedorainfracloud.org/coprs/ssweeny/system76-hwe/repo/fedora-${COPR_RELEASE}/ssweeny-system76-hwe-fedora-${COPR_RELEASE}.repo" "_copr_ssweeny-system76-hwe.repo" system76