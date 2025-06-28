import yaml
import json
import os
import sys

def get_kmods_to_build(kmod_type, fedora_major_version, kernel_flavor, image_name):
    kmods_to_build = []
    copr_repos_add_instructions = []
    dnf_install_commands = []
    akmods_force_commands = []

    # Load kmods.yaml
    with open('kmods.yaml', 'r') as f:
        kmods_config = yaml.safe_load(f)

    # Load cayo-images.yaml
    with open('cayo-images.yaml', 'r') as f:
        cayo_images_config = yaml.safe_load(f)

    # Get cppFlags for the current image
    cpp_flags = []
    if 'images' in cayo_images_config and image_name in cayo_images_config['images']:
        image_data = cayo_images_config['images'][image_name]
        if 'cppFlags' in image_data and image_data['cppFlags'] is not None:
            cpp_flags = [flag.upper() for flag in image_data['cppFlags']]

    # Process kmods
    if 'kmods' in kmods_config and kmod_type in kmods_config['kmods']:
        for kmod_json in kmods_config['kmods'][kmod_type]:
            name = kmod_json.get('name')
            copr_url = kmod_json.get('copr_url')
            copr_repo_file = kmod_json.get('copr_repo_file')
            mod_files = kmod_json.get('mod_files')
            conditions = kmod_json.get('conditions', {})
            cflags = kmod_json.get('cflags')

            build = True

            # Evaluate conditions
            if conditions:
                required_fedora_version_ge = conditions.get('fedora_major_version_ge')
                excluded_kernel_flavor = conditions.get('kernel_flavor_not_contains')
                required_release_ge = conditions.get('release_ge')
                copr_release_rawhide = conditions.get('copr_release_rawhide', False)
                kernel_not_contains = conditions.get('kernel_not_contains')
                dnf_search_displaylink_not_found = conditions.get('dnf_search_displaylink_not_found', False)

                if required_fedora_version_ge is not None:
                    if int(fedora_major_version.replace('stream', '')) < required_fedora_version_ge:
                        build = False

                if excluded_kernel_flavor is not None:
                    if excluded_kernel_flavor in kernel_flavor:
                        build = False

                # These conditions are assumed to be handled by CI or always true for local testing
                # as per the original shell script's comments.
                # if required_release_ge is not None:
                #     pass
                # if copr_release_rawhide:
                #     pass
                # if kernel_not_contains is not None:
                #     pass
                # if dnf_search_displaylink_not_found:
                #     pass

            # Check if kmod should be built based on cppFlags
            if cpp_flags and name.upper() not in cpp_flags:
                build = False

            if build:
                kmods_to_build.append(name)

                if copr_url and copr_repo_file:
                    # Replace variables in COPR_URL
                    formatted_copr_url = copr_url.replace('${RELEASE}', fedora_major_version).replace('${COPR_RELEASE}', fedora_major_version)
                    copr_repos_add_instructions.append(
                        f"RUN curl -fLO {formatted_copr_url} -o /tmp/ublue-os-akmods-addons/rpmbuild/SOURCES/{copr_repo_file} && "
                    )

                dnf_install_commands.append(f"dnf install -y akmod-{name} && ")
                # KERNEL_VERSION is not available in this script, so it's a placeholder.
                # The Makefile will need to provide this.
                akmods_force_commands.append(f"akmods --force --kmod {name} --target /usr/src/kernels/${{KERNEL_VERSION}} && ")

    print(f"KMODS_TO_BUILD={' '.join(kmods_to_build)!r}")
    print(f"COPR_REPOS_ADD_INSTRUCTIONS={'\n'.join(copr_repos_add_instructions)!r}")
    print(f"DNF_INSTALL_COMMANDS={'\n'.join(dnf_install_commands)!r}")
    print(f"AKMODS_FORCE_COMMANDS={'\n'.join(akmods_force_commands)!r}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python get_kmods_to_build.py <KMOD_TYPE> <FEDORA_MAJOR_VERSION> <KERNEL_FLAVOR> <IMAGE_NAME>")
        sys.exit(1)
    
    kmod_type = sys.argv[1]
    fedora_major_version = sys.argv[2]
    kernel_flavor = sys.argv[3]
    image_name = sys.argv[4]

    get_kmods_to_build(kmod_type, fedora_major_version, kernel_flavor, image_name)
