#!/bin/bash

KMOD_TYPE="$1"
FEDORA_MAJOR_VERSION="$2"
KERNEL_FLAVOR="$3"
IMAGE_NAME="$4"

KMODS_TO_BUILD=""
COPR_REPOS_ADD_INSTRUCTIONS=""
DNF_INSTALL_COMMANDS=""
AKMODS_FORCE_COMMANDS=""

# Get cppFlags for the current image
# Read kmods from YAML and process them
yq -o=json '.kmods.'\"${KMOD_TYPE}\"'[]' kmods.yaml | jq -c '.[]' | while read -r KMOD_JSON;
do
    NAME=$(echo "$KMOD_JSON" | jq -r '.name')
    COPR_URL=$(echo "$KMOD_JSON" | jq -r '.copr_url // "null"')
    COPR_REPO_FILE=$(echo "$KMOD_JSON" | jq -r '.copr_repo_file // "null"')
    MOD_FILES=$(echo "$KMOD_JSON" | jq -r '.mod_files[] // "null"')
    CONDITIONS=$(echo "$KMOD_JSON" | jq -r '.conditions // "null"')
    CFLAGS=$(echo "$KMOD_JSON" | jq -r '.cflags // "null"')

    BUILD=true

    # Evaluate conditions
    if [ "$CONDITIONS" != "null" ]; then
        REQUIRED_FEDORA_VERSION_GE=$(echo "$CONDITIONS" | jq -r '.fedora_major_version_ge // "null"')
        EXCLUDED_KERNEL_FLAVOR=$(echo "$CONDITIONS" | jq -r '.kernel_flavor_not_contains // "null"')
        REQUIRED_RELEASE_GE=$(echo "$CONDITIONS" | jq -r '.release_ge // "null"')
        COPR_RELEASE_RAWHIDE=$(echo "$CONDITIONS" | jq -r '.copr_release_rawhide // "false"')
        KERNEL_NOT_CONTAINS=$(echo "$CONDITIONS" | jq -r '.kernel_not_contains // "null"')
        DNF_SEARCH_DISPLAYLINK_NOT_FOUND=$(echo "$CONDITIONS" | jq -r '.dnf_search_displaylink_not_found // "false"')

        if [ "$REQUIRED_FEDORA_VERSION_GE" != "null" ]; then
            if [ "${FEDORA_MAJOR_VERSION}" -lt "${REQUIRED_FEDORA_VERSION_GE}" ]; then
                BUILD=false
            fi
        fi

        if [ "$EXCLUDED_KERNEL_FLAVOR" != "null" ]; then
            if [[ "${KERNEL_FLAVOR}" =~ "${EXCLUDED_KERNEL_FLAVOR}" ]]; then
                BUILD=false
            fi
        fi

        if [ "$REQUIRED_RELEASE_GE" != "null" ]; then
            # This condition needs to be evaluated against the actual release, which is not available here.
            # Assuming it's handled by CI or always true for local testing for now.
            :
        fi

        if [ "$COPR_RELEASE_RAWHIDE" == "true" ]; then
            # This condition needs to be evaluated against the actual COPR_RELEASE, which is not available here.
            # Assuming it's handled by CI or always true for local testing for now.
            :
        fi

        if [ "$KERNEL_NOT_CONTAINS" != "null" ]; then
            # This condition needs to be evaluated against the KERNEL variable, which is not available here.
            # Assuming it's handled by CI or always true for local testing for now.
            :
        fi

        if [ "$DNF_SEARCH_DISPLAYLINK_NOT_FOUND" == "true" ]; then
            # This condition needs to be evaluated by running dnf search, which is not feasible here.
            # Assuming it's handled by CI or always true for local testing for now.
            :
        fi
    fi

    # Check if kmod should be built based on cppFlags
    if [[ ! " ${CPP_FLAGS[@]} " =~ " ${NAME^^} " ]]; then
        BUILD=false
    fi

    if [ "$BUILD" = true ]; then
        KMODS_TO_BUILD+="$NAME "

        if [ "$COPR_URL" != "null" ] && [ "$COPR_REPO_FILE" != "null" ]; then
            COPR_REPOS_ADD_INSTRUCTIONS+="RUN curl -fLO $(echo "$COPR_URL" | sed "s|\\\${RELEASE}|${FEDORA_MAJOR_VERSION}|g" | sed "s|\\\${COPR_RELEASE}|${FEDORA_MAJOR_VERSION}|g") -o /tmp/ublue-os-akmods-addons/rpmbuild/SOURCES/${COPR_REPO_FILE} && \\\n"
        fi

        DNF_INSTALL_COMMANDS+="dnf install -y akmod-$NAME && \\\n"
        AKMODS_FORCE_COMMANDS+="akmods --force --kmod $NAME --target /usr/src/kernels/${KERNEL_VERSION} && \\\n"
    fi
done

echo "KMODS_TO_BUILD=\"$KMODS_TO_BUILD\""
echo "COPR_REPOS_ADD_INSTRUCTIONS=\"$COPR_REPOS_ADD_INSTRUCTIONS\""
echo "DNF_INSTALL_COMMANDS=\"$DNF_INSTALL_COMMANDS\""
echo "AKMODS_FORCE_COMMANDS=\"$AKMODS_FORCE_COMMANDS\""