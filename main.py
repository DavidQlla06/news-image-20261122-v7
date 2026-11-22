#!/usr/bin/env python3
"""Entry point: renders entry.png via generate.py (news-image-20261122 v7)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate import main

if __name__ == "__main__":
    main()
