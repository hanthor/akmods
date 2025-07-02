import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from build import main, get_latest_kernel_version

@pytest.fixture
def mock_config_for_kernel_lookup():
    return {
        'distros': {
            'fedora': {
                'versions': ['41', '42'],
                'image': 'quay.io/fedora/fedora'
            }
        }
    }

@pytest.fixture
def mock_full_build_config():
    return {
        'platforms': [
            {'amd64': {'default': True, 'alt_name': 'x86_64'}},
            {'amd64/v2': {'default': False, 'alt_name': 'x86_64_v2'}},
            {'arm64': {'default': True, 'alt_name': 'aarch64'}}
        ],
        'distros': {
            'centos': {'image': 'quay.io/centos-bootc/centos-bootc', 'versions': ['stream10']},
            'almalinux-kitten': {'image': 'quay.io/almalinuxorg/almalinux-bootc', 'versions': ['10-kitten'], 'extra_platforms': 'amd64/v2'},
            'almalinux': {'image': 'quay.io/almalinuxorg/almalinux-bootc', 'versions': [10], 'extra_platforms': 'amd64/v2'},
            'fedora': {'image': 'quay.io/fedora/fedora-bootc', 'versions': ['41', '42', 'rawhide']} # Added 41 for testing
        },
        'kmods': {
            'common': ['framework-laptop', 'kvmfr', 'openrazer', 'v4l2loopback', 'wl', 'xone'],
            'extra': ['ayaneo-platform', 'ayn-platform', 'bmi260', 'evdi', 'gcadapter_oc', 'gpd-fan', 'nct6687d', 'ryzen-smu', 'system76', 'system76-io', 'zenergy'],
            'nvidia': ['nvidia'],
            'zfs': ['zfs']
        }
    }

@patch('subprocess.run')
def test_get_latest_kernel_version(mock_run, mock_config_for_kernel_lookup):
    mock_run.return_value.stdout = """
Name        : kernel
Epoch       : 0
Version     : 6.15.3
Release     : 200.fc42
Architecture: x86_64
Size        : 12345
Source      : kernel-6.15.3-200.fc42.src.rpm
Repo        : @System
Summary     : The Linux kernel
URL         : http://www.kernel.org/
"""
    
    kernel_version = get_latest_kernel_version('fedora', '42', mock_config_for_kernel_lookup)
    assert kernel_version == '6.15.3-200.fc42.x86_64'
    mock_run.assert_called_once_with(
        ['podman', 'run', '--rm', 'quay.io/fedora/fedora:42', 'dnf', 'info', 'kernel'],
        capture_output=True, text=True, check=True
    )

@patch('build.list_images')
@patch('build.get_kmods_to_build')
@patch('build.KernelManager')
@patch('build.ContainerfileGenerator')
@patch('build.argparse.ArgumentParser')
@patch('build.get_latest_kernel_version')
@patch('builtins.open', new_callable=MagicMock)
@patch('yaml.safe_load')
def test_main(mock_yaml_safe_load, mock_open, mock_get_latest_kernel_version, mock_arg_parser, mock_containerfile_generator, mock_kernel_manager, mock_get_kmods_to_build, mock_list_images, mock_full_build_config):
    mock_list_images.return_value = ['fedora-42-x86_64-common']
    mock_get_kmods_to_build.return_value = ['framework-laptop', 'v4l2loopback']
    mock_get_latest_kernel_version.return_value = '6.9.0-1.fc42.x86_64'
    mock_yaml_safe_load.return_value = mock_full_build_config # Return the full config

    mock_args = MagicMock()
    mock_args.config = 'build_configurations.yaml'
    mock_args.images = None
    mock_args.kernel_version = None # Simulate no kernel version provided
    mock_args.kernel_flavor = 'main'
    mock_arg_parser.return_value.parse_args.return_value = mock_args

    main()

    mock_list_images.assert_called_once_with('build_configurations.yaml')
    mock_get_kmods_to_build.assert_called_once_with('common', '42', 'main', 'fedora-42-x86_64-common')
    mock_get_latest_kernel_version.assert_called_once_with('fedora', '42', mock_full_build_config)
    mock_kernel_manager.assert_called_once_with(
        kcwd=os.getcwd(),
        kernel_version='6.9.0-1.fc42.x86_64',
        kernel_flavor='main',
        builder_base='quay.io/fedora/fedora-bootc:42' # Corrected builder_base
    )
    mock_containerfile_generator.assert_called_once()