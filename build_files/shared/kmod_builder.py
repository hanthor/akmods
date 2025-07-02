import subprocess

class KmodBuilder:
    def __init__(self, mod_name, copr_url=None, copr_repo_file=None, mod_files=[]):
        self.mod_name = mod_name
        self.copr_url = copr_url
        self.copr_repo_file = copr_repo_file
        self.mod_files = mod_files
        self.arch = self.run_command("rpm -E '%_arch'").stdout.strip()
        self.kernel_name = self.run_command("rpm -q kernel --queryformat '%{NAME}'").stdout.strip()
        self.kernel_version = self.run_command(f"rpm -q {self.kernel_name} --queryformat '%{{VERSION}}-%{{RELEASE}}.%{{ARCH}}'").stdout.strip()
        self.release = self.run_command("rpm -E '%fedora'").stdout.strip()

    def run_command(self, command, check=True):
        return subprocess.run(command, shell=True, check=check, text=True, capture_output=True)

    def build_kmod(self):
        if self.copr_url and self.copr_repo_file:
            self.run_command(f'curl -LsSf -o /etc/yum.repos.d/{self.copr_repo_file} {self.copr_url}')
        
        self.run_command(f'dnf install -y akmod-{self.mod_name}-*.fc{self.release}.{self.arch}')
        self.run_command(f'akmods --force --kernels {self.kernel_version} --kmod {self.mod_name}')

        for mod_file in self.mod_files:
            self.run_command(f'modinfo /usr/lib/modules/{self.kernel_version}/extra/{self.mod_name}/{mod_file}.ko.xz')

        if self.copr_repo_file:
            self.run_command(f'rm -f /etc/yum.repos.d/{self.copr_repo_file}')
