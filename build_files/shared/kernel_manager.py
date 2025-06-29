import subprocess
import os

class KernelManager:
    def __init__(self, kcwd, kernel_version, kernel_flavor, builder_base, distro, build_tag='latest', use_test_certs=False):
        self.kcwd = kcwd
        self.kernel_version = kernel_version
        self.kernel_flavor = kernel_flavor
        self.builder_base = builder_base
        self.build_tag = build_tag
        self.arch = os.uname().machine
        self.container_id = None
        self.use_test_certs = use_test_certs
        self.distro = distro

    def __enter__(self):
        self._start_container()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_container()

    def _start_container(self):
        print(f"Starting persistent container {self.builder_base}...")
        podman_command = [
            'podman', 'run', '-d', '--privileged',
            '-v', f'{self.kcwd}:/mnt/host:rw,z',
            '-v', f'{self.kcwd}/kernel_cache:/tmp/kernel_cache:rw,z',
            '-w', '/mnt/host',
            self.builder_base,
            '/bin/bash', '-c', 'sleep infinity' # Keep container running
        ]
        result = subprocess.run(podman_command, check=True, text=True, capture_output=True)
        self.container_id = result.stdout.strip()
        print(f"Container started with ID: {self.container_id}")

        # Create necessary directories inside the container
        self.run_command('mkdir -p /etc/pki/kernel /etc/pki/kernel/public /etc/pki/kernel/private')

        # Ensure dnf-plugins-core is installed for config-manager
        self.run_command('dnf install -y dnf-plugins-core', in_container=True)

        

        if 'centos' in self.builder_base:
            self.run_command('dnf config-manager --set-enabled crb', in_container=True)
            centos_ver_result = self.run_command('rpm -E %centos', check=False, in_container=True)
            if centos_ver_result.returncode == 0:
                centos_ver = centos_ver_result.stdout.strip()
                self.run_command(f'dnf -y install epel-release', in_container=True)
                self.run_command('dnf config-manager --set-enabled epel', in_container=True)
                self.run_command('dnf clean all', in_container=True)
                self.run_command('dnf makecache', in_container=True)
            else:
                print("Warning: Could not determine CentOS version. Skipping EPEL installation.")

        # Install necessary tools inside the container
        self.run_command('dnf install -y --setopt=install_weak_deps=False openssl rpm-build', in_container=True)
        self.run_command('curl -#fL https://dl.fedoraproject.org/pub/epel/10.1/Everything/x86_64/Packages/s/sbsigntools-0.9.5-10.el10_1.x86_64.rpm -o /tmp/sbsigntools.rpm', in_container=True)
        self.run_command('rpm -i /tmp/sbsigntools.rpm', in_container=True)

    def _stop_container(self):
        if self.container_id:
            print(f"Stopping and removing container {self.container_id}...")
            subprocess.run(['podman', 'stop', self.container_id], check=False, capture_output=True)
            subprocess.run(['podman', 'rm', self.container_id], check=False, capture_output=True)
            self.container_id = None

    def run_command(self, command, check=True, in_container=True):
        print(f"Executing command: {command}")
        if in_container:
            if not self.container_id:
                raise RuntimeError("Container not started. Call _start_container() first.")
            podman_command = [
                'podman', 'exec', self.container_id,
                '/bin/bash', '-c', command
            ]
            try:
                result = subprocess.run(podman_command, check=check, text=True, capture_output=True)
                print(f"Command stdout: {result.stdout}")
                if result.stderr:
                    print(f"Command stderr: {result.stderr}")
                return result
            except subprocess.CalledProcessError as e:
                print(f"Command failed with exit code {e.returncode}")
                print(f"Command stdout: {e.stdout}")
                print(f"Command stderr: {e.stderr}")
                raise
        else:
            try:
                result = subprocess.run(command, shell=True, check=check, text=True, capture_output=True)
                print(f"Command stdout: {result.stdout}")
                if result.stderr:
                    print(f"Command stderr: {result.stderr}")
                return result
            except subprocess.CalledProcessError as e:
                print(f"Command failed with exit code {e.returncode}")
                print(f"Command stdout: {e.stdout}")
                print(f"Command stderr: {e.stderr}")
                raise

    def fetch_kernel(self):
        # Tools are now installed in _start_container
        self.download_kernel_rpms()

    def download_kernel_rpms(self):
        if self.distro == 'fedora':
            if self.kernel_flavor == 'asus':
                self.run_command('dnf copr enable -y lukenukem/asus-kernel')
                self.dnf_download_kernel_packages(packages_to_download=['kernel', 'kernel-core', 'kernel-modules', 'kernel-modules-core', 'kernel-modules-extra', 'kernel-devel', 'kernel-devel-matched', 'kernel-uki-virt'], flavor_prefix=None)
            elif self.kernel_flavor == 'surface':
                fedora_ver = self.run_command('rpm -E %fedora').stdout.strip()
                if int(fedora_ver) < 41:
                    self.run_command('dnf config-manager --add-repo=https://pkg.surfacelinux.com/fedora/linux-surface.repo')
                else:
                    self.run_command('dnf config-manager addrepo --from-repofile=https://pkg.surfacelinux.com/fedora/linux-surface.repo')
                self.dnf_download_kernel_packages(packages_to_download=['kernel', 'kernel-core', 'kernel-modules', 'kernel-modules-core', 'kernel-modules-extra', 'kernel-devel', 'kernel-devel-matched', 'kernel-uki-virt'], flavor_prefix='surface')
            elif self.kernel_flavor == 'bazzite':
                self.curl_download_kernel_packages(
                    f'https://github.com/bazzite-org/kernel-bazzite/releases/download/{self.build_tag}',
                    ['kernel', 'kernel-core', 'kernel-modules', 'kernel-modules-core', 'kernel-modules-extra', 'kernel-devel', 'kernel-devel-matched', 'kernel-uki-virt']
                )
            else: # main, coreos, etc. for Fedora
                kernel_major_minor_patch = self.kernel_version.split('-')[0]
                kernel_release_parts = self.kernel_version.split('-')[1].split('.')
                kernel_release = '.'.join(kernel_release_parts[:-1]) # Get all parts except the last (arch)
                packages = ['kernel', 'kernel-modules', 'kernel-modules-core', 'kernel-modules-extra', 'kernel-devel', 'kernel-devel-matched', 'kernel-uki-virt']
                base_url = f'https://kojipkgs.fedoraproject.org/packages/kernel/{kernel_major_minor_patch}/{kernel_release}/{self.arch}'
                for package in packages:
                    self.run_command(f'curl -#fL {base_url}/{package}-{self.kernel_version}.rpm -o /tmp/kernel_cache/{package}-{self.kernel_version}.rpm')
        elif self.distro == 'centos':
            if self.kernel_flavor == 'centos-hsk':
                self.run_command('dnf -y install centos-release-hyperscale-kernel')
                self.dnf_download_kernel_packages(packages_to_download=['kernel', 'kernel-core', 'kernel-modules', 'kernel-modules-core', 'kernel-modules-extra', 'kernel-devel', 'kernel-devel-matched', 'kernel-uki-virt'], flavor_prefix=None, repo='centos-hyperscale')
            else: # main, coreos, etc. for CentOS
                centos_ver = self.run_command('rpm -E %centos').stdout.strip()
                baseos_url = f'https://repo.almalinux.org/almalinux/{centos_ver}/BaseOS/{self.arch}/os/Packages'
                appstream_url = f'https://repo.almalinux.org/almalinux/{centos_ver}/AppStream/{self.arch}/os/Packages'

                self.curl_download_kernel_packages(
                    baseos_url,
                    ['kernel', 'kernel-core', 'kernel-modules', 'kernel-modules-core', 'kernel-modules-extra', 'kernel-uki-virt']
                )
                self.curl_download_kernel_packages(
                    appstream_url,
                    ['kernel-devel', 'kernel-devel-matched']
                )
        
        self.run_command(cmd)

    def curl_download_kernel_packages(self, base_url, packages):
        for package in packages:
            result = self.run_command(f'curl -#fL {base_url}/{package}-{self.kernel_version}.rpm -o /tmp/kernel_cache/{package}-{self.kernel_version}.rpm', check=False)
            if result.returncode != 0:
                print(f"Error downloading {package}-{self.kernel_version}.rpm: {result.stderr}")

    def sign_and_package_kernel(self, dual_sign=False):
        self.prepare_signing_keys()
        self.install_kernel_rpms()
        self.strip_signatures()
        self.sign_kernel_vmlinuz('/etc/pki/kernel/private/private_key.priv', '/etc/pki/kernel/public/public_key.crt')
        if dual_sign:
            self.prepare_dual_signing_keys()
            self.sign_kernel_vmlinuz('/etc/pki/kernel/private/private_key_2.priv', '/etc/pki/kernel/public/public_key_2.crt')
        self.rebuild_rpms()
        self.move_rpms()

    def prepare_signing_keys(self):
        priv_key_suffix = '.test' if self.use_test_certs else ''
        pub_key_suffix = '.test' if self.use_test_certs else ''

        # Copy certs from host to container's /etc/pki/kernel
        self.run_command(f'cp /mnt/host/certs/public_key.der{pub_key_suffix} /etc/pki/kernel/public_key.der')
        self.run_command(f'cp /mnt/host/certs/private_key.priv{priv_key_suffix} /etc/pki/kernel/private_key.priv')

        self.run_command(f'openssl pkey -inform DER -in /etc/pki/kernel/public_key.der -pubin -outform PEM -out /etc/pki/kernel/public_key.crt')
        self.run_command(f'install -Dm644 /etc/pki/kernel/public_key.crt /etc/pki/kernel/public/public_key.crt')
        self.run_command(f'install -Dm644 /etc/pki/kernel/private_key.priv /etc/pki/kernel/private/private_key.priv')

    def prepare_dual_signing_keys(self):
        priv_key_suffix = '.test' if self.use_test_certs else ''
        pub_key_suffix = '.test' if self.use_test_certs else ''

        # Copy certs from host to container's /etc/pki/kernel
        self.run_command(f'cp /mnt/host/certs/public_key_2.der{pub_key_suffix} /etc/pki/kernel/public_key_2.der')
        self.run_command(f'cp /mnt/host/certs/private_key_2.priv{priv_key_suffix} /etc/pki/kernel/private_key_2.priv')

        self.run_command(f'openssl x509 -in /etc/pki/kernel/public_key_2.der -out /etc/pki/kernel/public_key_2.crt')
        self.run_command(f'install -Dm644 /etc/pki/kernel/public_key_2.crt /etc/pki/kernel/public/public_key_2.crt')
        self.run_command(f'install -Dm644 /etc/pki/kernel/private_key_2.priv /etc/pki/kernel/private/private_key_2.priv')

    def install_kernel_rpms(self):
        # Simplified for now, will need to be more robust
        self.run_command(f'ls -l /tmp/kernel_cache/')
        self.run_command(f'dnf install -y /tmp/kernel_cache/*.rpm')

    def strip_signatures(self):
        if self.kernel_flavor not in ['main', 'coreos', 'centos']:
            result = self.run_command(f'sbverify --list /usr/lib/modules/{self.kernel_version}/vmlinuz', check=False)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if 'signature' in line:
                        self.run_command(f'sbattach --remove /usr/lib/modules/{self.kernel_version}/vmlinuz')

    def sign_kernel_vmlinuz(self, private_key, public_key):
        self.run_command(f'sbsign --key {private_key} --cert {public_key} /usr/lib/modules/{self.kernel_version}/vmlinuz --output /usr/lib/modules/{self.kernel_version}/vmlinuz')
        self.run_command(f'sbverify --list /usr/lib/modules/{self.kernel_version}/vmlinuz')

    def rebuild_rpms(self):
        self.run_command('ln -s / /tmp/buildroot')
        if 'surface' in self.kernel_flavor:
            self.run_command(f'rpmrebuild --additional=--buildroot=/tmp/buildroot --batch kernel-surface-core-{self.kernel_version}')
        else:
            self.run_command(f'rpmrebuild --additional=--buildroot=/tmp/buildroot --batch kernel-core-{self.kernel_version}')
        self.run_command(f'rm -f /usr/lib/modules/{self.kernel_version}/vmlinuz')
        self.run_command(f'dnf reinstall -y /tmp/kernel_cache/rpms/*.rpm /root/rpmbuild/RPMS/{self.arch}/kernel-*.rpm')
        self.run_command(f'sbverify --list /usr/lib/modules/{self.kernel_version}/vmlinuz')

    def move_rpms(self):
        self.run_command(f'mkdir -p /tmp/kernel_cache/rpms')
        self.run_command(f'mv /*.rpm /tmp/kernel_cache/rpms')
        if os.path.exists(f'/root/rpmbuild/RPMS/{self.arch}'):
            self.run_command(f'mv /root/rpmbuild/RPMS/{self.arch}/kernel-*.rpm /tmp/kernel_cache/rpms')