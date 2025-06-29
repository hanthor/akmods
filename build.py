import argparse
import yaml
import os
import subprocess
import re
from build_files.shared.list_images import list_images
from build_files.shared.get_kmods_to_build import get_kmods_to_build
from build_files.shared.kernel_manager import KernelManager
from build_files.shared.kmod_builder import KmodBuilder
from build_files.shared.containerfile_generator import ContainerfileGenerator

def get_latest_kernel_version(distro_name, distro_version, config, target_arch):
    # Find the specific distro and version entry in the config
    distro_entry = None
    for d_name, d_data in config['distros'].items():
        if d_name == distro_name:
            for version_entry in d_data['versions']:
                if str(distro_version) == str(version_entry):
                    distro_entry = d_data
                    break
            if distro_entry:
                break
    
    if not distro_entry:
        raise ValueError(f"Could not find distro {distro_name} version {distro_version} in build_configurations.yaml")

    # Check if latest_kernel_version is already cached
    if 'latest_kernel_version' in distro_entry:
        print(f"Using cached kernel version for {distro_name}:{distro_version}: {distro_entry['latest_kernel_version']}")
        return distro_entry['latest_kernel_version']

    base_image = f'{distro_entry['image']}:{distro_version}'
    print(f"Querying latest kernel version from {base_image}...")
    command = [
        'podman', 'run', '--rm',
        base_image,
        'dnf', 'info', 'kernel'
    ]
    print(f"Executing: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    
    version_match = re.search(r'Version\s*:\s*(.*)', result.stdout)
    release_match = re.search(r'Release\s*:\s*(.*)', result.stdout)
    arch_match = re.search(r'Architecture\s*:\s*(.*)', result.stdout)

    if version_match and release_match:
        kernel_version = f'{version_match.group(1).strip()}-{release_match.group(1).strip()}.{target_arch}'
        # Cache the fetched version
        distro_entry['latest_kernel_version'] = kernel_version
        return kernel_version
    else:
        raise ValueError(f"Could not parse kernel version from dnf info output: {result.stdout}")

def main():
    parser = argparse.ArgumentParser(description='Build OCI images for ublue-os akmods.')
    parser.add_argument('--config', default='build_configurations.yaml', help='Path to the build configurations file.')
    parser.add_argument('--images', nargs='+', help='A list of images to build. If not specified, all images will be built.')
    parser.add_argument('--dry-run', action='store_true', help='Do not execute podman commands.')
    parser.add_argument('--kernel-version', help='The kernel version to build against. Defaults to the latest kernel in the base image.')
    parser.add_argument('--kernel-flavor', default='main', help='The kernel flavor to build against.')
    parser.add_argument('--use-test-certs', action='store_true', help='Use test certificates for signing.')
    args = parser.parse_args()

    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    images_to_build = args.images or list_images(args.config)

    for image_name in images_to_build:
        print(f'\n--- Building image: {image_name} ---')
        # Split from the right to get kmod_group and arch
        parts = image_name.rsplit('-', 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid image_name format: {image_name}. Expected format: distro-version-arch-kmod_group")
        
        distro_version_part = parts[0]
        arch = parts[1]
        kmod_group = parts[2]

        distro = None
        version = None

        # Iterate through distros in config to find a match
        for d_name, d_data in config['distros'].items():
            if distro_version_part.startswith(d_name):
                potential_version_str = distro_version_part[len(d_name):]
                # Remove leading hyphen if present
                if potential_version_str.startswith('-'):
                    potential_version_str = potential_version_str[1:]

                for v_entry in d_data['versions']:
                    if str(v_entry) == potential_version_str:
                        distro = d_name
                        version = potential_version_str
                        break
            if distro and version is not None:
                break

        if not distro or version is None:
            raise ValueError(f"Could not parse distro and version from image_name: {image_name}")

        kernel_version = args.kernel_version
        if not kernel_version:
            kernel_version = get_latest_kernel_version(distro, version, config, arch)
            print(f"Dynamically determined kernel version: {kernel_version}")

        kmods = get_kmods_to_build(kmod_group, version, args.kernel_flavor, image_name)
        print(f"Kmods to build: {kmods}")

        # Create kernel_cache directory on host
        kernel_cache_path = os.path.join(os.getcwd(), 'kernel_cache')
        if os.path.exists(kernel_cache_path):
            import shutil
            shutil.rmtree(kernel_cache_path)
        os.makedirs(kernel_cache_path, exist_ok=True)
        print(f"Created kernel_cache directory: {kernel_cache_path}")

        # Determine the builder base image from the config
        builder_base_image = None
        for d_name, d_data in config['distros'].items():
            if d_name == distro:
                if str(version) in [str(v) for v in d_data['versions']]:
                    builder_base_image = f'{d_data['image']}:{version}'
                    break
        if not builder_base_image:
            raise ValueError(f"Could not determine builder base image for {distro}:{version}")

        if not args.dry_run:
            print("--- Fetching, signing, and packaging kernel ---")
            with KernelManager(
                kcwd=os.getcwd(),
                kernel_version=kernel_version,
                kernel_flavor=args.kernel_flavor,
                builder_base=builder_base_image, # Use the dynamically determined image
                use_test_certs=args.use_test_certs,
                distro=distro
            ) as kernel_manager:
                kernel_manager.fetch_kernel()
                kernel_manager.sign_and_package_kernel()
            print("--- Kernel operations complete ---")

        print("--- Generating Containerfile ---")
        containerfile_generator = ContainerfileGenerator(distro, version, arch, kmod_group, kmods)
        containerfile_generator.generate_containerfile(f'Containerfile.{image_name}')
        print(f"Generated Containerfile: Containerfile.{image_name}")

        # 3. Build the OCI image
        build_command = f'podman build -f Containerfile.{image_name} -t {image_name} .'
        print(f'Running build command: {build_command}')
        if not args.dry_run:
            subprocess.run(build_command, shell=True, check=True)

        # 4. Push the OCI image
        push_command = f'podman push {image_name}'
        print(f'Running push command: {push_command}')
        if not args.dry_run:
            subprocess.run(push_command, shell=True, check=True)

    # Write updated config back to file to save cached kernel versions
    with open(args.config, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

if __name__ == '__main__':
    main()
