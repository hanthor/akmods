import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from build_files.shared.kernel_manager import KernelManager

@pytest.fixture
def kernel_manager():
    return KernelManager('kcwd', '6.9.0-1.fc41.x86_64', 'main', 'test_builder_base')

@patch('subprocess.run')
def test_fetch_kernel_main(mock_run, kernel_manager):
    kernel_manager.fetch_kernel()
    mock_run.assert_any_call(['podman', 'run', '--rm', '--privileged', '-v', 'kcwd:/mnt/host:rw,z', '-v', 'kcwd/kernel_cache:/tmp/kernel_cache:rw,z', '-w', '/mnt/host', 'test_builder_base', '/bin/bash', '-c', 'dnf install -y --setopt=install_weak_deps=False dnf-plugins-core openssl'], check=True, text=True, capture_output=True)
    mock_run.assert_any_call(['podman', 'run', '--rm', '--privileged', '-v', 'kcwd:/mnt/host:rw,z', '-v', 'kcwd/kernel_cache:/tmp/kernel_cache:rw,z', '-w', '/mnt/host', 'test_builder_base', '/bin/bash', '-c', 'dnf -y install --setopt=install_weak_deps=False rpmrebuild sbsigntools'], check=True, text=True, capture_output=True)
    assert mock_run.call_count == 9 # 2 installs + 7 curl downloads

@patch('subprocess.run')
def test_fetch_kernel_asus(mock_run):
    km = KernelManager('kcwd', '6.9.0-1.fc41.x86_64', 'asus', 'test_builder_base')
    km.fetch_kernel()
    mock_run.assert_any_call(['podman', 'run', '--rm', '--privileged', '-v', 'kcwd:/mnt/host:rw,z', '-v', 'kcwd/kernel_cache:/tmp/kernel_cache:rw,z', '-w', '/mnt/host', 'test_builder_base', '/bin/bash', '-c', 'dnf copr enable -y lukenukem/asus-kernel'], check=True, text=True, capture_output=True)
    assert mock_run.call_count > 2

@patch('subprocess.run')
def test_fetch_kernel_centos(mock_run):
    km = KernelManager('kcwd', '5.14.0-362.8.1.el9_3.x86_64', 'centos', 'test_builder_base')
    # Mock the rpm -E %centos command
    mock_run.return_value.stdout = '9'
    km.fetch_kernel()
    mock_run.assert_any_call(['podman', 'run', '--rm', '--privileged', '-v', 'kcwd:/mnt/host:rw,z', '-v', 'kcwd/kernel_cache:/tmp/kernel_cache:rw,z', '-w', '/mnt/host', 'test_builder_base', '/bin/bash', '-c', 'dnf config-manager --set-enabled crb'], check=True, text=True, capture_output=True)
    assert mock_run.call_count > 2

@patch('subprocess.run')
@patch('os.path.exists')
def test_sign_and_package_kernel(mock_exists, mock_run, kernel_manager):
    mock_exists.return_value = True
    kernel_manager.sign_and_package_kernel()
    mock_run.assert_any_call(['podman', 'run', '--rm', '--privileged', '-v', 'kcwd:/mnt/host:rw,z', '-v', 'kcwd/kernel_cache:/tmp/kernel_cache:rw,z', '-w', '/mnt/host', 'test_builder_base', '/bin/bash', '-c', 'mkdir -p /tmp/kernel_cache/rpms'], check=True, text=True, capture_output=True)
    mock_run.assert_any_call(['podman', 'run', '--rm', '--privileged', '-v', 'kcwd:/mnt/host:rw,z', '-v', 'kcwd/kernel_cache:/tmp/kernel_cache:rw,z', '-w', '/mnt/host', 'test_builder_base', '/bin/bash', '-c', 'mv /*.rpm /tmp/kernel_cache/rpms'], check=True, text=True, capture_output=True)
    assert mock_run.call_count > 10 # A rough estimate of the number of commands

@patch('subprocess.run')
@patch('os.path.exists')
def test_sign_and_package_kernel_dual_sign(mock_exists, mock_run, kernel_manager):
    mock_exists.return_value = True
    kernel_manager.sign_and_package_kernel(dual_sign=True)
    assert mock_run.call_count > 15 # A rough estimate for dual signing