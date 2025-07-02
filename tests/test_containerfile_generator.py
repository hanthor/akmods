import pytest
from unittest.mock import mock_open, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from build_files.shared.containerfile_generator import ContainerfileGenerator

@pytest.fixture
def containerfile_generator():
    return ContainerfileGenerator('fedora-41-x86_64-common', ['framework-laptop', 'v4l2loopback'])

@patch('builtins.open', new_callable=mock_open, read_data='# KMOD_INSTALL_AND_BUILD_COMMANDS')
def test_generate_containerfile(mock_file, containerfile_generator):
    containerfile_generator.generate_containerfile('Containerfile.test')
    mock_file().write.assert_called_once_with('/tmp/build-kmod.sh framework-laptop && /tmp/build-kmod.sh v4l2loopback')
