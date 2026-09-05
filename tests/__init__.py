"""
Test suite initializer. Adds project root to sys.path.
"""

from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
