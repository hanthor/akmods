import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from build_files.shared.kernel_manager import KernelManager

@pytest.fixture
def kernel_manager():
    with patch('build_files.shared.kernel_manager.KernelManager._start_container') as mock_start_container:
        with patch('build_files.shared.kernel_manager.KernelManager._stop_container') as mock_stop_container:
            with patch('build_files.shared.kernel_manager.KernelManager.run_command') as mock_run_command:
                km = KernelManager('kcwd', '6.9.0-1.fc41.x86_64', 'main', 'test_builder_base', use_test_certs=True)
                km.container_id = 'mock_container_id' # Assign a mock container ID
                yield km

@patch('subprocess.run')
def test_fetch_kernel_main(mock_run, kernel_manager):
    kernel_manager.fetch_kernel()
    kernel_manager.run_command.assert_any_call('curl -#fLO https://kojipkgs.fedoraproject.org/packages/kernel/6.9.0/1.fc41/x86_64/kernel-6.9.0-1.fc41.x86_64.rpm')
    kernel_manager.run_command.assert_any_call('curl -#fLO https://kojipkgs.fedoraproject.org/packages/kernel/6.9.0/1.fc41/x86_64/kernel-modules-6.9.0-1.fc41.x86_64.rpm')
    kernel_manager.run_command.assert_any_call('curl -#fLO https://kojipkgs.fedoraproject.org/packages/kernel/6.9.0/1.fc41/x86_64/kernel-modules-core-6.9.0-1.fc41.x86_64.rpm')
    kernel_manager.run_command.assert_any_call('curl -#fLO https://kojipkgs.fedoraproject.org/packages/kernel/6.9.0/1.fc41/x86_64/kernel-modules-extra-6.9.0-1.fc41.x86_64.rpm')
    kernel_manager.run_command.assert_any_call('curl -#fLO https://kojipkgs.fedoraproject.org/packages/kernel/6.9.0/1.fc41/x86_64/kernel-devel-6.9.0-1.fc41.x86_64.rpm')
    kernel_manager.run_command.assert_any_call('curl -#fLO https://kojipkgs.fedoraproject.org/packages/kernel/6.9.0/1.fc41/x86_64/kernel-devel-matched-6.9.0-1.fc41.x86_64.rpm')
    kernel_manager.run_command.assert_any_call('curl -#fLO https://kojipkgs.fedoraproject.org/packages/kernel/6.9.0/1.fc41/x86_64/kernel-uki-virt-6.9.0-1.fc41.x86_64.rpm')
    assert kernel_manager.run_command.call_count == 7

@patch('subprocess.run')
def test_fetch_kernel_asus(mock_run, kernel_manager):
    kernel_manager.kernel_flavor = 'asus' # Set flavor for this test
    kernel_manager.fetch_kernel()
    kernel_manager.run_command.assert_any_call('dnf copr enable -y lukenukem/asus-kernel')
    assert kernel_manager.run_command.call_count > 0

@patch('subprocess.run')
def test_fetch_kernel_centos(mock_run, kernel_manager):
    kernel_manager.kernel_flavor = 'centos' # Set flavor for this test
    kernel_manager.run_command.return_value.stdout = '9'
    kernel_manager.fetch_kernel()
    kernel_manager.run_command.assert_any_call('rpm -E %centos')
    kernel_manager.run_command.assert_any_call('dnf config-manager --set-enabled crb')
    assert kernel_manager.run_command.call_count > 0

@patch('subprocess.run')
@patch('os.path.exists')
def test_sign_and_package_kernel(mock_exists, mock_run, kernel_manager):
    mock_exists.return_value = True
    kernel_manager.sign_and_package_kernel()
    kernel_manager.run_command.assert_any_call('cp /mnt/host/certs/public_key.der.test /etc/pki/kernel/public_key.der')
    kernel_manager.run_command.assert_any_call('cp /mnt/host/certs/private_key.priv.test /etc/pki/kernel/private_key.priv')
    assert kernel_manager.run_command.call_count > 0

@patch('subprocess.run')
@patch('os.path.exists')
def test_sign_and_package_kernel_dual_sign(mock_exists, mock_run, kernel_manager):
    mock_exists.return_value = True
    kernel_manager.sign_and_package_kernel(dual_sign=True)
    kernel_manager.run_command.assert_any_call('cp /mnt/host/certs/public_key_2.der.test /etc/pki/kernel/public_key_2.der')
    kernel_manager.run_command.assert_any_call('cp /mnt/host/certs/private_key_2.priv.test /etc/pki/kernel/private_key_2.priv')
    assert kernel_manager.run_command.call_count > 0