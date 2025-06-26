#!/bin/bash

set -eoux pipefail

RELEASE="$(rpm -E '%fedora')"

if [[ "${FEDORA_MAJOR_VERSION}" -ge 42 ]]; then
  if dnf search displaylink | grep -qv "displaylink"; then
    echo "Skipping build of evdi; displaylink net yet provided by negativo17"
    exit 0
  fi
fi

export CFLAGS="-fno-pie -no-pie"
/tmp/build-kmod.sh evdi "https://negativo17.org/repos/fedora-multimedia.repo" "negativo17-fedora-multimedia.repo" evdi
unset CFLAGS