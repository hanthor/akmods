import yaml
import sys

def list_images(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    platforms = {
        key: details['alt_name']
        for p in config['platforms']
        for key, details in p.items()
    }

    images = []
    for distro, details in config['distros'].items():
        for version in details['versions']:
            for platform, alt_name in platforms.items():
                if distro.startswith('almalinux') and 'extra_platforms' in details and platform not in details['extra_platforms']:
                    continue
                for kmod_group in config['kmods']:
                    images.append(f"{distro}-{version}-{alt_name}-{kmod_group}")
    return images

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <CONFIG_FILE>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    for image in list_images(config_file):
        print(image)
