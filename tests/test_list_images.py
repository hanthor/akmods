import pytest
from unittest.mock import mock_open, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from build_files.shared.list_images import list_images

@pytest.fixture
def mock_config():
    return {
        'platforms': [
            {'amd64': {'default': True, 'alt_name': 'x86_64'}},
            {'arm64': {'default': False, 'alt_name': 'aarch64'}},
        ],
        'distros': {
            'fedora': {'versions': ['40', '41']},
            'almalinux': {'versions': ['9'], 'extra_platforms': ['amd64']},
        },
        'kmods': {
            'nvidia': {},
            'zfs': {},
        },
    }

def test_list_images_basic(mock_config):
    with patch('builtins.open', mock_open(read_data="")):
        with patch('yaml.safe_load', return_value=mock_config):
            result = list_images('dummy_config.yaml')
            expected = [
                'fedora-40-x86_64-nvidia',
                'fedora-40-x86_64-zfs',
                'fedora-40-aarch64-nvidia',
                'fedora-40-aarch64-zfs',
                'fedora-41-x86_64-nvidia',
                'fedora-41-x86_64-zfs',
                'fedora-41-aarch64-nvidia',
                'fedora-41-aarch64-zfs',
                'almalinux-9-x86_64-nvidia',
                'almalinux-9-x86_64-zfs',
            ]
            assert sorted(result) == sorted(expected)

def test_list_images_empty_distros(mock_config):
    mock_config['distros'] = {}
    with patch('builtins.open', mock_open(read_data="")):
        with patch('yaml.safe_load', return_value=mock_config):
            assert list_images('dummy_config.yaml') == []

def test_list_images_empty_kmods(mock_config):
    mock_config['kmods'] = {}
    with patch('builtins.open', mock_open(read_data="")):
        with patch('yaml.safe_load', return_value=mock_config):
            assert list_images('dummy_config.yaml') == []

def test_list_images_platform_filtering(mock_config):
    mock_config['distros']['almalinux']['extra_platforms'] = ['amd64']
    with patch('builtins.open', mock_open(read_data="")):
        with patch('yaml.safe_load', return_value=mock_config):
            result = list_images('dummy_config.yaml')
            assert 'almalinux-9-aarch64-nvidia' not in result
            assert 'almalinux-9-aarch64-zfs' not in result