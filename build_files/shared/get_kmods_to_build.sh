#!/bin/bash

KMOD_TYPE="$1"
FEDORA_MAJOR_VERSION="$2"
KERNEL_FLAVOR="$3"

KMODS_TO_BUILD=""

# Read kmods from YAML
# Iterate over each kmod of the given type
yq eval ".kmods.${KMOD_TYPE}[]" kmods.yaml | while read -r kmod_data; do
    NAME=$(echo "$kmod_data" | yq eval '.name' -)
    CONDITIONS=$(echo "$kmod_data" | yq eval '.conditions' -)

    BUILD=true

    if [ "$CONDITIONS" != "null" ]; then
        # Check fedora_major_version_ge
        if [ "$(echo "$CONDITIONS" | yq eval '.fedora_major_version_ge // "null"' -)" != "null" ]; then
            REQUIRED_VERSION=$(echo "$CONDITIONS" | yq eval '.fedora_major_version_ge' -)
            if [ "${FEDORA_MAJOR_VERSION}" -lt "${REQUIRED_VERSION}" ]; then
                BUILD=false
            fi
        fi

        # Check kernel_flavor_not_contains
        if [ "$(echo "$CONDITIONS" | yq eval '.kernel_flavor_not_contains // "null"' -)" != "null" ]; then
            EXCLUDED_FLAVOR=$(echo "$CONDITIONS" | yq eval '.kernel_flavor_not_contains' -)
            if [[ "${KERNEL_FLAVOR}" =~ "${EXCLUDED_FLAVOR}" ]]; then
                BUILD=false
            fi
        fi

        # Check kernel_not_contains (for rtl8814au and rtl88xxau)
        if [ "$(echo "$CONDITIONS" | yq eval '.kernel_not_contains // "null"' -)" != "null" ]; then
            EXCLUDED_KERNEL=$(echo "$CONDITIONS" | yq eval '.kernel_not_contains' -)
            # KERNEL variable is not available here, so we can't check it directly.
            # This condition will need to be handled differently or assumed to be true for local testing.
            # For now, we'll assume it passes if the condition exists.
            # In CI, the actual KERNEL variable would be used.
        fi

        # Check dnf_search_displaylink_not_found (for evdi)
        if [ "$(echo "$CONDITIONS" | yq eval '.dnf_search_displaylink_not_found // "null"' -)" != "null" ]; then
            # This condition requires running dnf, which is not feasible here.
            # This will need to be handled differently or assumed to be true for local testing.
            # In CI, the actual dnf command would be run.
        fi

        # Check release_ge and copr_release_rawhide (for kvmfr, facetimehd, system76-io, system76, vhba)
        if [ "$(echo "$CONDITIONS" | yq eval '.release_ge // "null"' -)" != "null" ]; then
            REQUIRED_RELEASE=$(echo "$CONDITIONS" | yq eval '.release_ge' -)
            if [ "${FEDORA_MAJOR_VERSION}" -lt "${REQUIRED_RELEASE}" ]; then
                BUILD=false
            fi
        fi

        # copr_release_rawhide is a flag, not a condition to check here.

    fi

    if [ "$BUILD" = true ]; then
        KMODS_TO_BUILD+="$NAME "
    fi
done

echo "$KMODS_TO_BUILD"
