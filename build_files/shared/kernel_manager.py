import subprocess
import os

class KernelManager:
    def __init__(self, kcwd, kernel_version, kernel_flavor, builder_base, build_tag='latest'):
        self.kcwd = kcwd
        self.kernel_version = kernel_version
        self.kernel_flavor = kernel_flavor
        self.builder_base = builder_base
        self.build_tag = build_tag
        self.arch = os.uname().machine

    def run_command(self, command, check=True, in_container=True):
        print(f"Executing command: {command}")
        if in_container:
            podman_command = [
                'podman', 'run', '--rm', '--privileged',
                '-v', f'{self.kcwd}:/mnt/host:rw,z',
                '-v', f'{self.kcwd}/kernel_cache:/tmp/kernel_cache:rw,z', # Mount kernel_cache
                '-w', '/mnt/host',
                self.builder_base,
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
        self.run_command('dnf install -y --setopt=install_weak_deps=False dnf-plugins-core openssl rpmrebuild sbsigntools')

        self.download_kernel_rpms()

    def download_kernel_rpms(self):
        if self.kernel_flavor == 'asus':
            self.run_command('dnf copr enable -y lukenukem/asus-kernel')
            self.dnf_download_kernel_packages()
        elif self.kernel_flavor == 'surface':
            fedora_ver = self.run_command('rpm -E %fedora').stdout.strip()
            if int(fedora_ver) < 41:
                self.run_command('dnf config-manager --add-repo=https://pkg.surfacelinux.com/fedora/linux-surface.repo')
            else:
                self.run_command('dnf config-manager addrepo --from-repofile=https://pkg.surfacelinux.com/fedora/linux-surface.repo')
            self.dnf_download_kernel_packages('surface')
        elif self.kernel_flavor == 'bazzite':
            self.curl_download_kernel_packages(
                f'https://github.com/bazzite-org/kernel-bazzite/releases/download/{self.build_tag}',
                ['kernel', 'kernel-core', 'kernel-modules', 'kernel-modules-core', 'kernel-modules-extra', 'kernel-devel', 'kernel-devel-matched', 'kernel-uki-virt']
            )
        elif self.kernel_flavor == 'centos':
            centos_ver = self.run_command('rpm -E %centos').stdout.strip()
            self.curl_download_kernel_packages(
                f'https://mirror.stream.centos.org/{centos_ver}-stream/BaseOS/{self.arch}/os/Packages',
                ['kernel', 'kernel-core', 'kernel-modules', 'kernel-modules-core', 'kernel-modules-extra', 'kernel-uki-virt']
            )
            self.curl_download_kernel_packages(
                f'https://mirror.stream.centos.org/{centos_ver}-stream/AppStream/{self.arch}/os/Packages',
                ['kernel-devel', 'kernel-devel-matched']
            )
        elif self.kernel_flavor == 'centos-hsk':
            self.run_command('dnf -y install centos-release-hyperscale-kernel')
            self.dnf_download_kernel_packages(repo='centos-hyperscale')
        else: # main, coreos, etc.
            kernel_major_minor_patch = self.kernel_version.split('-')[0]
            kernel_release_parts = self.kernel_version.split('-')[1].split('.')
            kernel_release = '.'.join(kernel_release_parts[:-1]) # Get all parts except the last (arch)
            packages = ['kernel', 'kernel-modules', 'kernel-modules-core', 'kernel-modules-extra', 'kernel-devel', 'kernel-devel-matched', 'kernel-uki-virt']
            base_url = f'https://kojipkgs.fedoraproject.org/packages/kernel/{kernel_major_minor_patch}/{kernel_release}/{self.arch}'
            for package in packages:
                self.run_command(f'curl -#fLO {base_url}/{package}-{self.kernel_version}.rpm')

    def dnf_download_kernel_packages(self, flavor_prefix=None, repo=None):
        packages = ['kernel', 'kernel-modules', 'kernel-modules-core', 'kernel-modules-extra', 'kernel-devel', 'kernel-devel-matched', 'kernel-uki-virt']
        if flavor_prefix:
            packages = [f'{p}-{flavor_prefix}' for p in packages]
        
        cmd = 'dnf download -y'
        if repo:
            cmd += f' --enablerepo={repo}'
        cmd += ' ' + ' '.join([f'{p}-{self.kernel_version}' for p in packages])
        self.run_command(cmd)

    def curl_download_kernel_packages(self, base_url, packages):
        for package in packages:
            self.run_command(f'curl -#fLO {base_url}/{package}-{self.kernel_version}.rpm')

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
        if not os.path.exists(f'{self.kcwd}/certs/private_key.priv'):
            print("WARNING: Using test signing key.")
            self.run_command(f'cp {self.kcwd}/certs/private_key.priv.test {self.kcwd}/certs/private_key.priv', in_container=False)
            self.run_command(f'cp {self.kcwd}/certs/public_key.der.test {self.kcwd}/certs/public_key.der', in_container=False)
        self.run_command(f'openssl x509 -in {self.kcwd}/certs/public_key.der -out {self.kcwd}/certs/public_key.crt')
        self.run_command(f'install -Dm644 {self.kcwd}/certs/public_key.crt /etc/pki/kernel/public/public_key.crt')
        self.run_command(f'install -Dm644 {self.kcwd}/certs/private_key.priv /etc/pki/kernel/private/private_key.priv')

    def prepare_dual_signing_keys(self):
        if not os.path.exists(f'{self.kcwd}/certs/private_key_2.priv'):
            print("WARNING: Using test signing key for dual signing.")
            self.run_command(f'cp {self.kcwd}/certs/private_key_2.priv.test {self.kcwd}/certs/private_key_2.priv', in_container=False)
            self.run_command(f'cp {self.kcwd}/certs/public_key_2.der.test {self.kcwd}/certs/public_key_2.der', in_container=False)
        self.run_command(f'openssl x509 -in {self.kcwd}/certs/public_key_2.der -out {self.kcwd}/certs/public_key_2.crt')
        self.run_command(f'install -Dm644 {self.kcwd}/certs/public_key_2.crt /etc/pki/kernel/public/public_key_2.crt')
        self.run_command(f'install -Dm644 {self.kcwd}/certs/private_key_2.priv /etc/pki/kernel/private/private_key_2.priv')

    def install_kernel_rpms(self):
        # Simplified for now, will need to be more robust
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
        self.run_command(f'dnf reinstall -y /tmp/kernel_cache/*.rpm /root/rpmbuild/RPMS/{self.arch}/kernel-*.rpm')
        self.run_command(f'sbverify --list /usr/lib/modules/{self.kernel_version}/vmlinuz')

    def move_rpms(self):
        self.run_command(f'mkdir -p /tmp/kernel_cache/rpms')
        self.run_command(f'mv /*.rpm /tmp/kernel_cache/rpms')
        if os.path.exists(f'/root/rpmbuild/RPMS/{self.arch}'):
            self.run_command(f'mv /root/rpmbuild/RPMS/{self.arch}/kernel-*.rpm /tmp/kernel_cache/rpms')