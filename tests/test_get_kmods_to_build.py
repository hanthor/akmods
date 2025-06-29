import pytest
from unittest.mock import mock_open, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from build_files.shared.get_kmods_to_build import get_kmods_to_build, meets_conditions

@pytest.fixture
def mock_kmods_config():
    return {
        'kmods': {
            'common': [
                {'name': 'framework-laptop'},
                {'name': 'v4l2loopback'},
            ],
            'extra': [
                {
                    'name': 'evdi',
                    'conditions': {
                        'MAJOR_VERSION_ge': 42,
                        'kernel_flavor_not_contains': 'asus',
                    },
                },
            ],
        }
    }

def test_get_kmods_to_build_common(mock_kmods_config):
    with patch('builtins.open', mock_open(read_data="")):
        with patch('yaml.safe_load', return_value=mock_kmods_config):
            result = get_kmods_to_build('common', '41', 'generic', 'some-image')
            assert result == ['framework-laptop', 'v4l2loopback']

def test_get_kmods_to_build_extra_met_conditions(mock_kmods_config):
    with patch('builtins.open', mock_open(read_data="")):
        with patch('yaml.safe_load', return_value=mock_kmods_config):
            result = get_kmods_to_build('extra', '42', 'generic', 'some-image')
            assert result == ['evdi']

def test_get_kmods_to_build_extra_unmet_major_version(mock_kmods_config):
    with patch('builtins.open', mock_open(read_data="")):
        with patch('yaml.safe_load', return_value=mock_kmods_config):
            result = get_kmods_to_build('extra', '41', 'generic', 'some-image')
            assert result == []

def test_get_kmods_to_build_extra_unmet_kernel_flavor(mock_kmods_config):
    with patch('builtins.open', mock_open(read_data="")):
        with patch('yaml.safe_load', return_value=mock_kmods_config):
            result = get_kmods_to_build('extra', '42', 'asus', 'some-image')
            assert result == []

def test_meets_conditions_no_conditions():
    kmod = {'name': 'test-kmod'}
    assert meets_conditions(kmod, '42', 'generic', 'some-image') is True

def test_meets_conditions_major_version_ge_met():
    kmod = {'name': 'test-kmod', 'conditions': {'MAJOR_VERSION_ge': 42}}
    assert meets_conditions(kmod, '42', 'generic', 'some-image') is True

def test_meets_conditions_major_version_ge_unmet():
    kmod = {'name': 'test-kmod', 'conditions': {'MAJOR_VERSION_ge': 43}}
    assert meets_conditions(kmod, '42', 'generic', 'some-image') is False

def test_meets_conditions_kernel_flavor_not_contains_met():
    kmod = {'name': 'test-kmod', 'conditions': {'kernel_flavor_not_contains': 'asus'}}
    assert meets_conditions(kmod, '42', 'generic', 'some-image') is True

def test_meets_conditions_kernel_flavor_not_contains_unmet():
    kmod = {'name': 'test-kmod', 'conditions': {'kernel_flavor_not_contains': 'generic'}}
    assert meets_conditions(kmod, '42', 'generic', 'some-image') is False