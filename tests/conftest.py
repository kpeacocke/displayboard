# tests/conftest.py
import sys
import os

# Add project src directory to sys.path so imports of "skaven" work in tests
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
sys.path.insert(0, SRC_DIR)
