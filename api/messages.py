# Import handler from data.py to share the same database
import sys
import os

# Add api directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import and use the same handler from data.py
from data import handler
