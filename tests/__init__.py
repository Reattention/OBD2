"""Test package initialization"""

import sys
import os

# Add the parent directory to the path so we can import the obd2_diagnostics package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))