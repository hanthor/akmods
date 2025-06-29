import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from build_files.shared.kmod_builder import KmodBuilder

@pytest.fixture
def kmod_builder():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = 'test'
        builder = KmodBuilder('my-kmod', copr_url='my-copr-url', copr_repo_file='my-repo-file', mod_files=['my-mod-file'])
        return builder

@patch('subprocess.run')
def test_build_kmod(mock_run, kmod_builder):
    kmod_builder.build_kmod()
    mock_run.assert_any_call('curl -LsSf -o /etc/yum.repos.d/my-repo-file my-copr-url', shell=True, check=True, text=True, capture_output=True)
    mock_run.assert_any_call('dnf install -y akmod-my-kmod-*.fctest.test', shell=True, check=True, text=True, capture_output=True)
    mock_run.assert_any_call('akmods --force --kernels test --kmod my-kmod', shell=True, check=True, text=True, capture_output=True)
    mock_run.assert_any_call('modinfo /usr/lib/modules/test/extra/my-kmod/my-mod-file.ko.xz', shell=True, check=True, text=True, capture_output=True)
    mock_run.assert_any_call('rm -f /etc/yum.repos.d/my-repo-file', shell=True, check=True, text=True, capture_output=True)
