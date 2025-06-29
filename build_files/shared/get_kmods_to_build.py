import yaml
import sys

def get_kmods_to_build(kmod_type, fedora_major_version, kernel_flavor, image_name, kmods_config_file='kmods.yaml'):
    with open(kmods_config_file, 'r') as f:
        kmods_config = yaml.safe_load(f)

    kmods_to_build = []
    if kmod_type in kmods_config['kmods']:
        for kmod in kmods_config['kmods'][kmod_type]:
            if meets_conditions(kmod, fedora_major_version, kernel_flavor, image_name):
                kmods_to_build.append(kmod['name'])
    return kmods_to_build

def meets_conditions(kmod, fedora_major_version, kernel_flavor, image_name):
    if 'conditions' not in kmod:
        return True

    conditions = kmod['conditions']
    if 'MAJOR_VERSION_ge' in conditions and fedora_major_version.isdigit() and int(fedora_major_version) < conditions['MAJOR_VERSION_ge']:
        return False
    if 'kernel_flavor_not_contains' in conditions and conditions['kernel_flavor_not_contains'] in kernel_flavor:
        return False
    # Add other condition checks here as needed

    return True

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(f"Usage: python {sys.argv[0]} <KMOD_TYPE> <FEDORA_MAJOR_VERSION> <KERNEL_FLAVOR> <IMAGE_NAME>")
        sys.exit(1)
    
    kmod_type, fedora_major_version, kernel_flavor, image_name = sys.argv[1:]
    kmods = get_kmods_to_build(kmod_type, fedora_major_version, kernel_flavor, image_name)
    print(' '.join(kmods))