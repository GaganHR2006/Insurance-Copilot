"""
Data Loader Service - Loads and caches JSON data files from the data/ directory.
"""

import json
import os
from typing import List

_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

_hospitals_cache: List[dict] = []
_policies_cache: List[dict] = []
_treatments_cache: List[dict] = []


def _load_json(filename: str) -> List[dict]:
    """Load a JSON file from the data directory."""
    filepath = os.path.join(_BASE_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_hospitals() -> List[dict]:
    """Load and cache hospitals data from hospitals.json."""
    global _hospitals_cache
    if not _hospitals_cache:
        _hospitals_cache = _load_json("hospitals.json")
    return _hospitals_cache


def load_policies() -> List[dict]:
    """Load and cache policies data from policies.json."""
    global _policies_cache
    if not _policies_cache:
        _policies_cache = _load_json("policies.json")
    return _policies_cache


def load_treatments() -> List[dict]:
    """Load and cache treatments data from treatments.json."""
    global _treatments_cache
    if not _treatments_cache:
        _treatments_cache = _load_json("treatments.json")
    return _treatments_cache
