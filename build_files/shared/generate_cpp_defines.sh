#!/bin/bash

# This script generates cpp #define directives based on build_configurations.yaml

CONFIG_FILE="build_configurations.yaml"

# Read platforms
PLATFORMS=$(yq -r '.platforms[] | .alt_name' "$CONFIG_FILE")

# Read distros and their versions
for distro in $(yq -r '.distros | keys | .[]' "$CONFIG_FILE");
do
    # Read the versions for each distro
    eval "${distro^^}_VERSIONS=$(yq -r ".distros.${distro}.versions[]" "$CONFIG_FILE")"
done

# Read distro-specific extra platforms
for distro in $(yq -r '.distros | keys | .[]' "$CONFIG_FILE");
do
    # Read the extra platforms for each distro
    eval "${distro^^}_EXTRA_PLATFORMS=$(yq -r ".distros.${distro}.extra_platforms | join(',')" "$CONFIG_FILE")"
done

# Read kmod groups
KMOD_GROUPS=$(yq -r '.kmods | keys | .[]' "$CONFIG_FILE")

# Function to generate defines
generate_defines() {
    local distro_name=$1
    local versions=$2
    local platforms=$3
    local kmod_groups=$4
    local extra_platforms=$5

    for version in $versions;
do
        for platform in $platforms;
        # Check if the platform is defined as default platform.default=true and add it platforms if so
        do platform=$(yq -r ".platforms[] | select(.default == true) | .[] " "$CONFIG_FILE")

        do
            # Check for extra platforms
            if [[  -n "$extra_platforms" ]]; then
                # If extra platforms are defined, append them to the platforms list
                platform="${platform},${extra_platforms}"
            fi

            for kmod_group in $kmod_groups;
            do
                # Define format: DISTRO_VERSION_PLATFORM_KMODGROUP
                DEFINE_NAME="$(echo ${distro_name}_${version}_${platform}_${kmod_group} | tr '[:lower:]' '[:upper:]' | tr '-' '_' | tr '/' '_')"
                echo "#define ${DEFINE_NAME} 1"
            done
        done
    done
}

# Generate defines for Fedora
generate_defines "fedora" "$MAJOR_VERSIONS" "$PLATFORMS" "$KMOD_GROUPS"

# Generate defines for CentOS
generate_defines "centos" "$CENTOS_VERSIONS" "$PLATFORMS" "$KMOD_GROUPS"

# Generate defines for AlmaLinux
generate_defines "almalinux" "$ALMALINUX_VERSIONS" "$PLATFORMS" "$KMOD_GROUPS"
