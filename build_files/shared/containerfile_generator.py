import os

class ContainerfileGenerator:
    def __init__(self, distro, version, arch, kmod_group, kmods_to_build, containerfile_in_path='Containerfile.in'):
        self.distro = distro
        self.version = version
        self.arch = arch
        self.kmod_group = kmod_group
        self.kmods_to_build = kmods_to_build
        self.containerfile_in_path = containerfile_in_path

    def generate_containerfile(self, output_path):
        with open(self.containerfile_in_path, 'r') as f:
            containerfile_in = f.read()

        # Use self.distro, self.version, self.arch, self.kmod_group directly
        kmod_install_commands = []
        for kmod in self.kmods_to_build:
            kmod_install_commands.append(f'/tmp/build-kmod.sh {kmod}')

        containerfile = containerfile_in.replace(
            '# KMOD_INSTALL_AND_BUILD_COMMANDS',
            'set -x && ' + ' && '.join(kmod_install_commands)
        )

        with open(output_path, 'w') as f:
            f.write(containerfile)