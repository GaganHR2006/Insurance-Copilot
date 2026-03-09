"""
Hospitals Router — Returns hospitals from the merged dataset
(hospitals.json + hospital_network.json), with real bed data from
bed_availability.json, filtered by city and treatment.
"""

import json
import os
from typing import Optional, List, Any, Dict

from fastapi import APIRouter

from services.data_loader import (
    get_beds_for_hospital,
    get_network_for_hospital,
    load_hospital_network,
)

from pydantic import BaseModel, Field

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# ── City aliases so Bengaluru == Bangalore, Bombay == Mumbai, etc. ────────────
CITY_ALIASES: Dict[str, str] = {
    "bangalore": "Bangalore", "bengaluru": "Bangalore",
    "delhi": "Delhi", "new delhi": "Delhi",
    "mumbai": "Mumbai", "bombay": "Mumbai",
    "chennai": "Chennai", "madras": "Chennai",
    "hyderabad": "Hyderabad",
    "kolkata": "Kolkata", "calcutta": "Kolkata",
    "pune": "Pune", "ahmedabad": "Ahmedabad",
    "jaipur": "Jaipur", "lucknow": "Lucknow",
    "chandigarh": "Chandigarh", "bhopal": "Bhopal",
    "surat": "Surat", "kochi": "Kochi", "cochin": "Kochi",
    "nagpur": "Nagpur",
}

# ── Specialty → searchable treatment terms ────────────────────────────────────
SPECIALTY_TO_TREATMENTS: Dict[str, List[str]] = {
    "Cardiology":         ["cardiac surgery", "cardiac bypass", "angioplasty", "heart"],
    "Cardiac surgery":    ["cardiac surgery", "cardiac bypass"],
    "Oncology":           ["chemotherapy", "cancer", "oncology"],
    "Orthopedics":        ["knee replacement", "hip replacement", "orthopedic"],
    "Nephrology":         ["dialysis", "kidney", "renal"],
    "Transplant Surgery": ["organ transplant", "transplant"],
    "Ophthalmology":      ["cataract surgery", "cataract", "eye"],
    "Gynecology":         ["maternity", "gynecology", "obstetrics"],
    "General Surgery":    ["appendectomy", "surgery"],
    "Neurology":          ["neurology", "brain", "spine"],
    "Gastroenterology":   ["gastroenterology", "liver", "stomach"],
    "Pulmonology":        ["pulmonology", "lung", "respiratory"],
    "Urology":            ["urology", "urinary"],
    "Psychiatry":         ["psychiatry", "mental health"],
    "Pediatrics":         ["pediatrics", "children"],
    "Dermatology":        ["dermatology", "skin"],
    "ENT":                ["ent", "ear", "nose", "throat"],
}


def canon_city(raw: str) -> str:
    return CITY_ALIASES.get(raw.strip().lower(), raw.strip().title())


def norm(text: str) -> str:
    return " ".join(text.lower().strip().split())


def treatment_match(query: str, treatment_list: List[str]) -> bool:
    """
    Flexible matching: exact, partial containment, shared keywords.
    Handles 'Cardiac Surgery' matching 'cardiac surgery' and vice-versa.
    """
    q = norm(query)
    for t in treatment_list:
        t_n = norm(str(t))
        if q == t_n:
            return True
        if q in t_n or t_n in q:
            return True
        if set(q.split()) & set(t_n.split()):
            return True
    return False


def specialties_to_treatments(specialties: List[str]) -> List[str]:
    """Convert network specialties to searchable treatment strings."""
    out = set()
    for s in specialties:
        for term in SPECIALTY_TO_TREATMENTS.get(s, [norm(s)]):
            out.add(term)
    return sorted(out)


def bed_status(available: int, total: int) -> str:
    if total == 0:
        return "No Data"
    ratio = available / total
    if ratio > 0.5:
        return "Readily Available"
    elif ratio > 0.2:
        return "Limited Availability"
    else:
        return "Critical — Very Few Beds"


def load_all_hospitals() -> List[Dict[str, Any]]:
    """
    Build a unified hospital list from hospitals.json + hospital_network.json.
    hospitals.json entries take priority (they have richer data).
    Deduplication: by (normalised name, canonical city).
    """
    # ── Primary: hospitals.json ──────────────────────────────────────────────
    primary_path = os.path.join(DATA_DIR, "hospitals.json")
    primary: List[Dict] = []
    if os.path.exists(primary_path):
        with open(primary_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        primary = raw if isinstance(raw, list) else raw.get("hospitals", [])

    seen: Dict[str, bool] = {}
    merged: List[Dict[str, Any]] = []

    for h in primary:
        key = (norm(h.get("name", "")), canon_city(h.get("city", "")))
        if key not in seen:
            seen[key] = True
            merged.append({
                "_source":        "primary",
                "id":             h.get("id", ""),
                "name":           h.get("name", "Unknown"),
                "city":           h.get("city", ""),
                "treatments":     [norm(t) for t in h.get("treatments", [])],
                "network_policies": h.get("network_policies", []),
                "rating":         h.get("rating", 4.0),
                "icu_beds":       h.get("icu_beds", 10),
                "general_beds":   h.get("general_beds", 40),
            })

    # ── Secondary: hospital_network.json ────────────────────────────────────
    network_index = load_hospital_network()
    seen_ids = set()

    for key_str, item in network_index.items():
        # Only process once per unique record
        hid = item.get("id", item.get("hospital_id", ""))
        if hid in seen_ids:
            continue
        seen_ids.add(hid)

        name = item.get("hospital", item.get("name", "Unknown"))
        city = item.get("city", "")
        dedup_key = (norm(name), canon_city(city))
        if dedup_key in seen:
            continue
        seen[dedup_key] = True
        specialties = item.get("specialties", [])
        merged.append({
            "_source":        "network",
            "id":             hid,
            "name":           name,
            "city":           city,
            "treatments":     specialties_to_treatments(specialties),
            "specialties_raw": specialties,
            "network_policies": item.get("cashless_insurers", []),
            "rating":         4.0,
            "icu_beds":       None,   # will be filled from bed_availability
            "general_beds":   None,
        })

    return merged


class HospitalSearchRequest(BaseModel):
    city: Optional[str] = None
    treatment: Optional[str] = None
    pdf_policy: Optional[Dict[str, Any]] = Field(default_factory=dict)


@router.post("/search")
async def search_hospitals(request: HospitalSearchRequest):
    """
    Merged hospital search across hospitals.json + hospital_network.json.
    Beds joined from bed_availability.json; networks from hospital_network.json.
    Both city and treatment matching are case-insensitive with aliases.
    """
    city = request.city
    treatment = request.treatment
    all_hospitals = load_all_hospitals()
    pdf_policy    = request.pdf_policy or {}
    user_insurer  = pdf_policy.get("insurer")
    user_covered  = [norm(t) for t in pdf_policy.get("covered_treatments", [])]

    # ── Filter ────────────────────────────────────────────────────────────────
    results: List[Dict[str, Any]] = []

    for h in all_hospitals:
        # City filter
        if city and canon_city(city) != canon_city(h["city"]):
            continue

        # Treatment filter
        if treatment and not treatment_match(treatment, h["treatments"]):
            continue

        # ── Bed data ──────────────────────────────────────────────────────────
        # hospital_network.json entries have pre-embedded flat bed fields.
        # hospitals.json entries have flat icu_beds/general_beds integers.
        if "icu_beds_total" in h:
            # Network hospital: fields embedded during pre-processing
            icu_total  = h["icu_beds_total"]
            icu_avail  = h["icu_beds_available"]
            gen_total  = h["gen_beds_total"]
            gen_avail  = h["gen_beds_available"]
        else:
            # Primary hospital (hospitals.json): use flat int fields
            icu_total  = h.get("icu_beds") or 10
            gen_total  = h.get("general_beds") or 40
            # Try live bed_availability.json join as a bonus
            bed_rec = get_beds_for_hospital(str(h.get("id", "")), h["name"])
            if bed_rec:
                icu_obj   = bed_rec.get("icu_beds", {})
                gen_obj   = bed_rec.get("general_beds", {})
                icu_total = icu_obj.get("total", icu_total) if isinstance(icu_obj, dict) else icu_total
                icu_avail = icu_obj.get("available", icu_total) if isinstance(icu_obj, dict) else icu_total
                gen_total = gen_obj.get("total", gen_total) if isinstance(gen_obj, dict) else gen_total
                gen_avail = gen_obj.get("available", gen_total) if isinstance(gen_obj, dict) else gen_total
            else:
                icu_avail = icu_total
                gen_avail = gen_total

        total_beds = (icu_total + gen_total) or 1
        occupied   = (icu_total - icu_avail) + (gen_total - gen_avail)
        occ_pct    = round(occupied / total_beds * 100, 1)

        # ── Network/policy join ───────────────────────────────────────────────
        net_rec = get_network_for_hospital(str(h["id"]), h["name"])
        if net_rec:
            accepted_policies = net_rec.get("cashless_insurers",
                                net_rec.get("network_policies", h["network_policies"]))
        else:
            accepted_policies = h["network_policies"]

        # ── PDF policy context ────────────────────────────────────────────────
        accepts_user = (
            any(user_insurer.lower() in p.lower() for p in accepted_policies)
            if user_insurer else None
        )
        treatment_covered = (
            any(treatment_match(treatment, [t]) for t in user_covered)
            if (treatment and user_covered) else None
        )
        mentioned_in_pdf = any(
            kw in h["name"].lower()
            for kw in [k for k in pdf_policy.get("network_hospitals", [])]
        ) if pdf_policy else False

        results.append({
            "id":       h["id"],
            "name":     h["name"],
            "city":     h["city"],
            "rating":   h["rating"],
            "treatments": h["treatments"],
            "bed_availability": {
                "icu": {
                    "total":        icu_total,
                    "available":    icu_avail,
                    "status":       bed_status(icu_avail, icu_total),
                    "percent_free": round(icu_avail / max(icu_total, 1) * 100, 1),
                },
                "general": {
                    "total":        gen_total,
                    "available":    gen_avail,
                    "status":       bed_status(gen_avail, gen_total),
                    "percent_free": round(gen_avail / max(gen_total, 1) * 100, 1),
                },
                "occupancy_rate_percent": occ_pct,
            },
            "network_policies": accepted_policies,
            "policy_context": {
                "user_insurer":                 user_insurer,
                "hospital_accepts_user_policy": accepts_user,
                "treatment_covered_in_policy":  treatment_covered,
                "hospital_mentioned_in_pdf":    mentioned_in_pdf,
                "policy_name":                  pdf_policy.get("policy_name"),
                "sum_insured":                  pdf_policy.get("sum_insured"),
                "waiting_period_days":          pdf_policy.get("waiting_period_days"),
            },
        })

    # ── Sort ──────────────────────────────────────────────────────────────────
    results.sort(key=lambda h: (
        not h["policy_context"].get("hospital_mentioned_in_pdf"),
        not (h["policy_context"].get("hospital_accepts_user_policy") or False),
        h.get("_source") == "network",
        -h.get("rating", 0),
    ))

    # ── Coverage warning ──────────────────────────────────────────────────────
    coverage_warning = None
    if treatment and user_covered and not any(
        treatment_match(treatment, [t]) for t in user_covered
    ):
        coverage_warning = (
            f"'{treatment}' does not appear covered under your "
            f"{pdf_policy.get('insurer', 'uploaded')} policy. "
            f"Verify with your insurer before booking."
        )

    return {
        "hospitals": results,
        "count":     len(results),
        "filters_applied": {"city": city, "treatment": treatment},
        "policy_context": {
            "pdf_uploaded":    bool(pdf_policy),
            "user_insurer":    user_insurer,
            "coverage_warning": coverage_warning,
            "treatments_covered_in_policy": pdf_policy.get("covered_treatments", []),
        },
    }
