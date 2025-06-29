#!/bin/sh

set -oeux pipefail

RELEASE="$(rpm -E '%fedora')"

/tmp/build-kmod.sh xone "https://copr.fedorainfracloud.org/coprs/ublue-os/akmods/repo/fedora-${RELEASE}/ublue-os-akmods-fedora-${RELEASE}.repo" "_copr_ublue-os-akmods.repo" xone-dongle xone-gip xone-gip-gamepad xone-gip-headset xone-gip-chatpad xone-gip-madcatz-strat xone-gip-madcatz-glam xone-gip-pdp-jaguar