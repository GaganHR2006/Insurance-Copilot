"""
Data Loader Service — Loads JSON data files from the data/ directory.
No module-level caching so JSON edits are always picked up without restart.
Provides helper functions to join bed_availability + hospital_network data.
"""

import json
import os
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _load(filename: str):
    """Load raw JSON from the data directory. Returns None if file missing."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"[WARN] File not found: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Primary datasets ──────────────────────────────────────────────────────────

def load_hospitals() -> list:
    """Load hospitals.json — returns a flat list."""
    raw = _load("hospitals.json")
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("hospitals", list(raw.values())[0] if raw else [])
    return []


def load_policies() -> list:
    raw = _load("policies.json")
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return list(raw.values())
    return []


def load_treatments() -> list:
    raw = _load("treatments.json")
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return list(raw.values())
    return []


# ── Lookup datasets (bed availability + hospital network) ─────────────────────

def _index_list(raw: list, *id_fields) -> dict:
    """
    Build a lookup dict from a list of records.
    Keys: every id_field value found + lowercased name/hospital field values.
    """
    index = {}
    for item in raw:
        # Index by ID fields (e.g. hospital_id, id)
        for fld in id_fields:
            val = item.get(fld)
            if val:
                index[str(val).upper()] = item   # H001, h001 → "H001"
                index[str(val).lower()] = item   # store both cases
        # Index by name fields for fuzzy lookup
        for name_fld in ("hospital", "name", "hospital_name"):
            nm = item.get(name_fld, "")
            if nm:
                index[nm.lower().strip()] = item
    return index


def load_bed_availability() -> dict:
    """
    Returns a dict keyed by hospital_id (uppercase) AND hospital name (lower).
    bed_availability.json schema:
      { hospital_id, hospital, city,
        icu_beds: {total, available},
        general_beds: {total, available} }
    """
    raw = _load("bed_availability.json")
    if isinstance(raw, list):
        return _index_list(raw, "hospital_id", "id")
    if isinstance(raw, dict):
        return raw
    return {}


def load_hospital_network() -> dict:
    """
    Returns a dict keyed by hospital_id (uppercase) AND hospital name (lower).
    hospital_network.json schema:
      { id, hospital, city, cashless_insurers: [...], specialties: [...] }
    """
    raw = _load("hospital_network.json")
    if isinstance(raw, list):
        return _index_list(raw, "id", "hospital_id")
    if isinstance(raw, dict):
        return raw
    return {}


# ── Convenience join helpers ──────────────────────────────────────────────────

def _fuzzy_get(index: dict, hospital_id: str, hospital_name: str) -> Optional[dict]:
    """Try exact ID → exact name → partial name."""
    # Exact ID (upper and lower)
    val = index.get(hospital_id.upper()) or index.get(hospital_id.lower())
    if val:
        return val
    # Exact name
    nm = hospital_name.lower().strip()
    val = index.get(nm)
    if val:
        return val
    # Partial: check if any key is a substring of the name or vice-versa
    for key, record in index.items():
        if len(key) > 4 and (key in nm or nm in key):
            return record
    return None


def get_beds_for_hospital(hospital_id: str, hospital_name: str) -> Optional[dict]:
    """Return bed_availability record for a given hospital, or None."""
    return _fuzzy_get(load_bed_availability(), hospital_id, hospital_name)


def get_network_for_hospital(hospital_id: str, hospital_name: str) -> Optional[dict]:
    """Return hospital_network record for a given hospital, or None."""
    return _fuzzy_get(load_hospital_network(), hospital_id, hospital_name)


# ── Session-level PDF policy store (disk-backed, survives hot-reload) ─────────

_SESSION_FILE = os.path.join(DATA_DIR, "session_policy.json")
_policy_store = {"data": {}}

def store_pdf_policy(policy_data: dict):
    """Persist extracted PDF policy to memory AND disk."""
    _policy_store["data"] = policy_data
    try:
        from utils.debug_logger import log
        log("store_pdf_policy", {
            "insurer": policy_data.get("insurer"),
            "policy_name": policy_data.get("policy_name"),
            "freebies_count": len(policy_data.get("freebies", [])),
            "covered_treatments": policy_data.get("covered_treatments", []),
            "keys_stored": list(policy_data.keys())
        })
    except ImportError:
        pass
        
    try:
        with open(_SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(policy_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Could not persist session_policy.json: {e}")

def get_pdf_policy() -> dict:
    """Return uploaded PDF policy data, loading from disk if memory is empty."""
    if not _policy_store["data"]:
        try:
            if os.path.exists(_SESSION_FILE):
                with open(_SESSION_FILE, "r", encoding="utf-8") as f:
                    _policy_store["data"] = json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load session_policy.json: {e}")
            
    data = _policy_store["data"]
    try:
        from utils.debug_logger import log
        log("get_pdf_policy", {
            "has_data": bool(data),
            "insurer": data.get("insurer"),
            "freebies_count": len(data.get("freebies", []))
        })
    except ImportError:
        pass
    return data

def clear_pdf_policy():
    """Clear stored PDF policy from memory and disk."""
    _policy_store["data"] = {}
    try:
        if os.path.exists(_SESSION_FILE):
            os.remove(_SESSION_FILE)
    except Exception as e:
        print(f"[WARN] Could not delete session_policy.json: {e}")

