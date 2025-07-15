"""
Unit test fixtures
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def mock_proc_stat():
    """Mock /proc/stat content for CPU testing"""
    return "cpu  123456 0 654321 999999 0 0 0 0 0 0\n"


@pytest.fixture
def mock_proc_meminfo():
    """Mock /proc/meminfo content for memory testing"""
    return """MemTotal:        8000000 kB
MemFree:         2000000 kB
MemAvailable:    4000000 kB
Buffers:          500000 kB
Cached:          1500000 kB
"""


@pytest.fixture
def mock_proc_diskstats():
    """Mock /proc/diskstats content for disk I/O testing"""
    return """   8       0 sda 1000 0 0 0 2000 0 0 0 0 0 0 0 0 0 0 0 0
   8       1 sda1 100 0 0 0 200 0 0 0 0 0 0 0 0 0 0 0 0
"""


@pytest.fixture
def mock_proc_net_dev():
    """Mock /proc/net/dev content for network I/O testing"""
    return """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:    1000     100    0    0    0     0          0         0     1000     100    0    0    0     0       0          0
  eth0:   50000     500    0    0    0     0          0         0    25000     250    0    0    0     0       0          0
"""


@pytest.fixture
def mock_psutil_unavailable():
    """Mock psutil as unavailable for testing fallback mechanisms"""
    with patch("monitoring.PSUTIL_AVAILABLE", False):
        yield


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing"""
    with patch("builtins.open", mock_open()) as mock_file:
        yield mock_file
