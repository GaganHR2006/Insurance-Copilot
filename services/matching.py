"""
Shared matching utilities — token-based fuzzy matching for hospital, policy, and treatment lookups.

Strategy:
  - Split both query and target into words (tokens)
  - A query matches a target if:
      (a) any query word appears in the target string  (broad search)
      OR
      (b) any target word appears in the query string  (handles synonyms / abbreviations)
  - This avoids the "apollo bangalore" ∉ "apollo hospitals bangalore" substring failure.
"""

from typing import List, Optional


def _tokens(text: str) -> List[str]:
    """Return lowercased, whitespace-split tokens from a string."""
    return text.lower().split()


def fuzzy_match(query: str, target: str) -> bool:
    """
    Return True if the query meaningfully overlaps with the target string.
    Works bi-directionally so both short and long queries resolve correctly.
    """
    q_lower = query.lower()
    t_lower = target.lower()

    # Exact or direct substring (fastest path)
    if q_lower in t_lower or t_lower in q_lower:
        return True

    # Token overlap: any word from the query appears in the target (or vice-versa)
    q_tokens = set(_tokens(q_lower))
    t_tokens = set(_tokens(t_lower))
    return bool(q_tokens & t_tokens)


def match_hospital(query: str, hospitals: List[dict]) -> Optional[dict]:
    """Return the best-matching hospital for a query string, or None."""
    query_lower = query.lower()

    # 1. Prefer an exact ID match
    for h in hospitals:
        if h["id"].lower() == query_lower:
            return h

    # 2. Token-based name match (score by number of matching tokens — pick best)
    q_tokens = set(_tokens(query_lower))
    best, best_score = None, 0
    for h in hospitals:
        t_tokens = set(_tokens(h["name"].lower()))
        score = len(q_tokens & t_tokens)
        if score > best_score:
            best_score = score
            best = h

    return best if best_score > 0 else None


def match_policy(query: str, policies: List[dict]) -> Optional[dict]:
    """Return the best-matching policy for a query string, or None."""
    query_lower = query.lower()

    # Exact provider name match first
    for p in policies:
        if p["provider"].lower() == query_lower:
            return p

    # Token-based match across name + provider
    q_tokens = set(_tokens(query_lower))
    best, best_score = None, 0
    for p in policies:
        combined = p["name"].lower() + " " + p["provider"].lower()
        t_tokens = set(_tokens(combined))
        score = len(q_tokens & t_tokens)
        if score > best_score:
            best_score = score
            best = p

    return best if best_score > 0 else None


def match_treatment(query: str, treatments: List[dict]) -> Optional[dict]:
    """Return the best-matching treatment for a query string, or None."""
    query_lower = query.lower()

    # Direct substring (e.g. "knee" in "knee replacement")
    for t in treatments:
        if query_lower in t["name"].lower() or t["name"].lower() in query_lower:
            return t

    # Token overlap
    q_tokens = set(_tokens(query_lower))
    best, best_score = None, 0
    for t in treatments:
        t_tokens = set(_tokens(t["name"].lower()))
        score = len(q_tokens & t_tokens)
        if score > best_score:
            best_score = score
            best = t

    return best if best_score > 0 else None


def treatment_matches_list(query: str, items: List[str]) -> bool:
    """
    Check if a treatment query matches any item in a list
    (e.g. covered_treatments, exclusions).
    Uses bidirectional matching so 'knee' matches 'knee replacement' and vice versa.
    """
    q_lower = query.lower()
    for item in items:
        item_lower = item.lower()
        if q_lower in item_lower or item_lower in q_lower:
            return True
        # Token overlap
        q_tokens = set(_tokens(q_lower))
        i_tokens = set(_tokens(item_lower))
        if q_tokens & i_tokens:
            return True
    return False
