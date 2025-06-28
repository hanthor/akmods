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

def get_latest_kernel_version(distro_name, distro_version, config):
    # Find the base image for the given distro and version
    base_image = None
    for d_name, d_data in config['distros'].items():
        if d_name == distro_name:
            if int(distro_version) in d_data['versions'] or distro_version in d_data['versions']:
                base_image = f'{d_data['image']}:{distro_version}'
                break
    
    if not base_image:
        raise ValueError(f"Could not find base image for {distro_name}:{distro_version} in build_configurations.yaml")

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

    if version_match and release_match and arch_match:
        version = version_match.group(1).strip()
        release = release_match.group(1).strip()
        arch = arch_match.group(1).strip()
        return f'{version}-{release}.{arch}'
    else:
        raise ValueError(f"Could not parse kernel version from dnf info output: {result.stdout}")

def main():
    parser = argparse.ArgumentParser(description='Build OCI images for ublue-os akmods.')
    parser.add_argument('--config', default='build_configurations.yaml', help='Path to the build configurations file.')
    parser.add_argument('--images', nargs='+', help='A list of images to build. If not specified, all images will be built.')
    parser.add_argument('--dry-run', action='store_true', help='Do not execute podman commands.')
    parser.add_argument('--kernel-version', help='The kernel version to build against. Defaults to the latest kernel in the base image.')
    parser.add_argument('--kernel-flavor', default='main', help='The kernel flavor to build against.')
    args = parser.parse_args()

    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    images_to_build = args.images or list_images(args.config)

    for image_name in images_to_build:
        print(f'\n--- Building image: {image_name} ---')
        distro, version, arch, kmod_group = image_name.split('-')

        kernel_version = args.kernel_version
        if not kernel_version:
            kernel_version = get_latest_kernel_version(distro, version, config)
            print(f"Dynamically determined kernel version: {kernel_version}")

        kmods = get_kmods_to_build(kmod_group, version, args.kernel_flavor, image_name)
        print(f"Kmods to build: {kmods}")

        # Create kernel_cache directory on host
        kernel_cache_path = os.path.join(os.getcwd(), 'kernel_cache')
        os.makedirs(kernel_cache_path, exist_ok=True)
        print(f"Created kernel_cache directory: {kernel_cache_path}")

        print("--- Fetching, signing, and packaging kernel ---")
        kernel_manager = KernelManager(
            kcwd=os.getcwd(),
            kernel_version=kernel_version,
            kernel_flavor=args.kernel_flavor,
            builder_base=f'quay.io/fedora/fedora:{version}' # Use a full Fedora image for kernel operations
        )
        kernel_manager.fetch_kernel()
        kernel_manager.sign_and_package_kernel()
        print("--- Kernel operations complete ---")

        print("--- Generating Containerfile ---")
        containerfile_generator = ContainerfileGenerator(image_name, kmods)
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

if __name__ == '__main__':
    main()