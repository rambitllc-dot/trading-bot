"""Tests never write to the real monitor.db or output files: every test session gets its own temporary ones."""
import os
import tempfile

from monitor import config

config.DB_FILE = os.path.join(tempfile.mkdtemp(), "test_monitor.db")
config.OUTPUT_DIR = tempfile.mkdtemp()
