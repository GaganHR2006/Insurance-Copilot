import sys
import os

# Add parent directory to path so all imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app
