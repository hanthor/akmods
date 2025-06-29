#!/bin/sh

set -oeux pipefail

KERNEL="$(rpm -q "${KERNEL_NAME}" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"
RELEASE="$(rpm -E '%fedora')"

if [[ "${KERNEL}" =~ "6.8" ]]; then
  echo "SKIPPED BUILD of rtl8814au: compile failure on kernel 6.8 as of 2024-03-17"
  exit 0
fi

/tmp/build-kmod.sh rtl8814au "https://copr.fedorainfracloud.org/coprs/ublue-os/akmods/repo/fedora-${RELEASE}/ublue-os-akmods-fedora-${RELEASE}.repo" "_copr_ublue-os-akmods.repo" rtl8814au