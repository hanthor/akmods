#!/bin/sh

set -oeux pipefail

MOD_NAME=$1
COPR_URL=${2:-}
COPR_REPO_FILE=${3:-}
shift 3
MOD_FILES=("$@")

ARCH="$(rpm -E '%_arch')"
KERNEL="$(rpm -q "${KERNEL_NAME}" --queryformat '%{VERSION}-%{RELEASE}.%{ARCH}')"
RELEASE="$(rpm -E '%fedora')"

if [ -n "${COPR_URL}" ]; then
    if [ -n "${COPR_REPO_FILE}" ]; then
        curl -LsSf -o "/etc/yum.repos.d/${COPR_REPO_FILE}" "${COPR_URL}"
    else
        echo "COPR_REPO_FILE must be provided if COPR_URL is set"
        exit 1
    fi
fi

dnf install -y \
    "akmod-${MOD_NAME}-*.fc${RELEASE}.${ARCH}"
akmods --force --kernels "${KERNEL}" --kmod "${MOD_NAME}"

for MOD_FILE in "${MOD_FILES[@]}"; do
    modinfo "/usr/lib/modules/${KERNEL}/extra/${MOD_NAME}/${MOD_FILE}.ko.xz" > /dev/null \
    || (find "/var/cache/akmods/${MOD_NAME}/" -name \*.log -print -exec cat {} \; && exit 1)
done

if [ -n "${COPR_REPO_FILE}" ]; then
    rm -f "/etc/yum.repos.d/${COPR_REPO_FILE}"
fi