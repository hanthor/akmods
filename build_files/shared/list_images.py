import yaml
import sys

def list_images(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    platforms_map = {}
    for p_item in config['platforms']:
        # p_item is a dictionary like {'amd64': {'default': True, 'alt_name': 'x86_64'}}
        platform_key = list(p_item.keys())[0]
        platform_details = p_item[platform_key]
        platforms_map[platform_key] = platform_details['alt_name']

    distros_config = config['distros']
    kmod_groups = config['kmods'].keys()

    image_names = []

    for distro_name, distro_data in distros_config.items():
        versions = distro_data['versions']
        extra_platforms = distro_data.get('extra_platforms', '').split(',')
        if extra_platforms == ['']:
            extra_platforms = []

        for version in versions:
            for platform_key, platform_alt_name in platforms_map.items():
                # Apply platform filtering for almalinux-kitten and almalinux
                if distro_name.startswith('almalinux') and extra_platforms and platform_key not in extra_platforms:
                    continue

                for kmod_group in kmod_groups:
                    # Construct image name based on the pattern used in the project
                    # This might need adjustment based on the actual image naming convention
                    # For now, let's just list the components for now.
                    image_name_components = [
                        distro_name,
                        str(version),
                        platform_alt_name,
                        kmod_group
                    ]
                    image_names.append('-'.join(image_name_components))

    for name in image_names:
        print(name)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python list_images.py <CONFIG_FILE>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    list_images(config_file)