import yaml
import sys

def generate_cpp_defines(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    platforms = {list(p.keys())[0]: list(p.values())[0]['alt_name'] for p in config['platforms']}
    distros = config['distros']
    kmod_groups = config['kmods'].keys()

    defines = []

    for distro_name, distro_data in distros.items():
        image_base = distro_data.get('image', '')
        versions = distro_data['versions']
        extra_platforms = distro_data.get('extra_platforms', '').split(',')
        if extra_platforms == ['']:
            extra_platforms = []

        for version in versions:
            for platform_key, platform_alt_name in platforms.items():
                # Check if this platform is allowed for this distro, especially for extra_platforms
                if distro_name.startswith('almalinux') and extra_platforms and platform_key not in extra_platforms:
                    continue

                for kmod_group in kmod_groups:
                    define_name = f"{distro_name}_{version}_{platform_alt_name}_{kmod_group}"
                    defines.append(f"#define {define_name.upper().replace('.', '_').replace('-', '_').replace('/', '_')} 1")

    for define in defines:
        print(define)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_cpp_defines.py <CONFIG_FILE>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    generate_cpp_defines(config_file)
