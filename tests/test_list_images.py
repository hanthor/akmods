import pytest
import yaml
import sys
import os
from unittest.mock import mock_open, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from build_files.shared.list_images import list_images

@pytest.fixture
def mock_config_content():
    return """
platforms:
  - amd64:
      default: true
      alt_name: x86_64
  - arm64:
      default: false
      alt_name: aarch64
distros:
  fedora:
    versions:
      - "40"
      - "41"
  almalinux:
    versions:
      - "9"
    extra_platforms: "amd64"
kmods:
  nvidia:
    description: "NVIDIA graphics drivers"
  zfs:
    description: "ZFS file system"
"""

def test_list_images_basic(mock_config_content, capsys):
    with patch("builtins.open", mock_open(read_data=mock_config_content)):
        list_images("dummy_config.yaml")
        captured = capsys.readouterr()
        expected_output = [
            "fedora-40-x86_64-nvidia",
            "fedora-40-x86_64-zfs",
            "fedora-40-aarch64-nvidia",
            "fedora-40-aarch64-zfs",
            "fedora-41-x86_64-nvidia",
            "fedora-41-x86_64-zfs",
            "fedora-41-aarch64-nvidia",
            "fedora-41-aarch64-zfs",
            "almalinux-9-x86_64-nvidia",
            "almalinux-9-x86_64-zfs",
        ]
        assert sorted(captured.out.strip().split('\n')) == sorted(expected_output)

def test_list_images_empty_distros(capsys):
    empty_config = """
platforms:
  - amd64:
      default: true
      alt_name: x86_64
distros: {}
kmods:
  nvidia:
    description: "NVIDIA graphics drivers"
"""
    with patch("builtins.open", mock_open(read_data=empty_config)):
        list_images("dummy_config.yaml")
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

def test_list_images_empty_kmods(capsys):
    empty_config = """
platforms:
  - amd64:
      default: true
      alt_name: x86_64
distros:
  fedora:
    versions:
      - "40"
kmods: {}
"""
    with patch("builtins.open", mock_open(read_data=empty_config)):
        list_images("dummy_config.yaml")
        captured = capsys.readouterr()
        assert captured.out.strip() == ""
