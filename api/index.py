"""
api/index.py — Vercel Python serverless entry point
Imports the Flask `app` object so Vercel can call it as a WSGI handler.
"""

import sys
import os

# Make the project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: F401  — Vercel needs this name exactly
