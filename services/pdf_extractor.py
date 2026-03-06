"""
PDF Policy Extractor - Extracts structured policy info from raw PDF text.
Uses regex and keyword matching (no LLM) for fast, deterministic extraction.
"""

import re
from typing import Optional

# Known insurer name aliases for fuzzy matching
INSURER_ALIASES = {
    "star health":               "Star Health",
    "star health and allied":    "Star Health",
    "hdfc ergo":                 "HDFC Ergo",
    "hdfc":                      "HDFC Ergo",
    "bajaj allianz":             "Bajaj Allianz",
    "bajaj":                     "Bajaj Allianz",
    "care health":               "Care Health",
    "care":                      "Care Health",
    "niva bupa":                 "Niva Bupa",
    "bupa":                      "Niva Bupa",
    "united india":              "United India",
    "new india":                 "New India Assurance",
    "oriental":                  "Oriental Insurance",
    "national insurance":        "National Insurance",
}

KNOWN_TREATMENTS = [
    "knee replacement", "cardiac surgery", "cardiac bypass",
    "angioplasty", "dialysis", "chemotherapy", "cataract",
    "cataract surgery", "organ transplant", "maternity",
    "hip replacement", "appendectomy", "cancer treatment",
    "bypass surgery", "coronary", "fracture", "surgery",
]

HOSPITAL_KEYWORDS = [
    "apollo", "fortis", "manipal", "kokilaben", "max hospital",
    "aiims", "medanta", "columbia asia", "narayana", "lilavati",
    "breach candy", "hinduja", "wockhardt", "aster", "care hospital",
    "rainbow", "cloudnine", "yashoda", "continental",
]


def extract_policy_info(pdf_text: str) -> dict:
    """
    Extracts structured policy info from raw PDF text.
    Returns dict with: insurer, policy_name, covered_treatments,
    network_hospitals, sum_insured, waiting_period_days, room_rent_cap.
    """
    text_lower = pdf_text.lower()
    result = {
        "insurer": None,
        "policy_name": None,
        "covered_treatments": [],
        "network_hospitals": [],
        "sum_insured": None,
        "waiting_period_days": None,
        "room_rent_cap": None,
        "raw_text_snippet": pdf_text[:500],
    }

    # ── Insurer name ──────────────────────────────────────
    for alias, canonical in INSURER_ALIASES.items():
        if alias in text_lower:
            result["insurer"] = canonical
            break

    # ── Policy name ───────────────────────────────────────
    policy_patterns = [
        r"policy\s+name[:\s]+([A-Za-z\s\-]+)",
        r"product\s+name[:\s]+([A-Za-z\s\-]+)",
        r"plan\s+name[:\s]+([A-Za-z\s\-]+)",
        r"([\w\s]+(?:health|medical|care|plus|shield|protect)\s*(?:plan|policy|cover))",
    ]
    for pattern in policy_patterns:
        match = re.search(pattern, text_lower)
        if match:
            result["policy_name"] = match.group(1).strip().title()
            break

    # ── Covered treatments ────────────────────────────────
    found_treatments = []
    for treatment in KNOWN_TREATMENTS:
        if treatment in text_lower:
            idx = text_lower.find(treatment)
            surrounding = text_lower[max(0, idx - 60): idx + 60]
            if not any(word in surrounding for word in
                       ["exclud", "not cover", "not eligible", "exception"]):
                found_treatments.append(treatment)
    result["covered_treatments"] = list(set(found_treatments))

    # ── Sum insured ───────────────────────────────────────
    sum_patterns = [
        r"sum\s+insured[:\s₹rs.]*\s*([\d,]+)",
        r"coverage\s+amount[:\s₹rs.]*\s*([\d,]+)",
        r"insured\s+amount[:\s₹rs.]*\s*([\d,]+)",
    ]
    for pattern in sum_patterns:
        match = re.search(pattern, text_lower)
        if match:
            result["sum_insured"] = match.group(1).replace(",", "")
            break

    # ── Waiting period ────────────────────────────────────
    wait_patterns = [
        r"waiting\s+period\s+(?:of\s+)?(\d+)\s*(days|months|years)",
        r"waiting\s+period[:\s]*(\d+)\s*(days|months|years)",
        r"(\d+)[- ]day\s+waiting",
        r"(\d+)[- ]month\s+waiting",
    ]
    for pattern in wait_patterns:
        match = re.search(pattern, text_lower)
        if match:
            val = int(match.group(1))
            groups = match.groups()
            unit = groups[1] if len(groups) > 1 else "days"
            if "month" in unit:
                val *= 30
            elif "year" in unit:
                val *= 365
            result["waiting_period_days"] = val
            break

    # ── Room rent cap ─────────────────────────────────────
    rent_patterns = [
        r"room\s+rent\s+(?:cap|limit)\s+(?:of\s+)?(?:rs\.?|₹|inr)?\s*([\d,]+)",
        r"room\s+rent[:\srs.₹]*\s*([\d,]+)\s*(?:per day|/day|daily)?",
        r"room\s+rent\s+limit[:\srs.₹]*\s*([\d,]+)",
    ]
    for pattern in rent_patterns:
        match = re.search(pattern, text_lower)
        if match:
            result["room_rent_cap"] = match.group(1).replace(",", "")
            break

    # ── Mentioned hospitals ───────────────────────────────
    found_hospitals = []
    for hospital in HOSPITAL_KEYWORDS:
        if hospital in text_lower:
            found_hospitals.append(hospital.title())
    result["network_hospitals"] = found_hospitals

    # ── Exclusions ────────────────────────────────────────
    EXCLUSION_KEYWORDS = [
        "cosmetic", "dental", "lasik", "vision correction",
        "maternity", "fertility", "ivf", "obesity",
        "self-inflicted", "war", "adventure sports",
        "organ transplant", "hiv", "aids", "congenital",
        "hormone", "sex change", "experimental",
    ]
    found_exclusions = []
    excl_idx = text_lower.find("exclusion")
    excl_section = (
        text_lower[excl_idx: excl_idx + 1500] if excl_idx != -1 else ""
    )
    search_zone = excl_section if excl_section else text_lower
    for kw in EXCLUSION_KEYWORDS:
        if kw in search_zone:
            found_exclusions.append(kw)
    result["exclusions"] = found_exclusions

    # ── Sub-limits ────────────────────────────────────────
    sub_limits = {}
    sublimit_idx = text_lower.find("sub-limit")
    if sublimit_idx == -1:
        sublimit_idx = text_lower.find("sub limit")
    if sublimit_idx != -1:
        sl_section = text_lower[sublimit_idx: sublimit_idx + 800]
        sl_pattern = (
            r"(?:maximum\s+payout\s+of\s+(?:rs\.?|₹|inr)?\s*([\d,]+)\s+for\s+([\w\s]+))|"
            r"([\w\s]+?)\s*[:\-\u2013]\s*"
            r"(?:upto?|maximum|max|limit of)?\s*"
            r"(?:rs\.?|₹|inr)?\s*([\d,]+)\s*"
            r"(?:per|/|\s)?(?:claim|year|day|annum)?"
        )
        for match in re.findall(sl_pattern, sl_section):
            if match[0]: # matched alternative 1: payout of X for Y
                amount, name = match[0], match[1]
            else: # matched alternative 2: Y: X
                name, amount = match[2], match[3]
            
            name_clean = name.strip().strip("-:").strip()
            if 2 < len(name_clean) < 40:
                sub_limits[name_clean] = amount.replace(",", "")
    result["sub_limits"] = sub_limits

    # ── Age limits ────────────────────────────────────────
    age_pattern = r"(?:entry\s+)?age[:\s]*(\d+)\s*(?:to|-|\u2013)\s*(\d+)"
    age_match = re.search(age_pattern, text_lower)
    if age_match:
        result["min_age"] = int(age_match.group(1))
        result["max_age"] = int(age_match.group(2))
    else:
        result["min_age"] = 18
        result["max_age"] = 65

    result["freebies"] = extract_freebies(text_lower)
    result["freebies_count"] = len(result["freebies"])

    return result


def extract_freebies(pdf_text: str) -> list:
    import re
    text_lower = pdf_text.lower()
    found = []

    # Map of benefit_id -> (label, icon, category, keywords, frequency)
    BENEFITS = [
        ("health_checkup", "Free Annual Health Check-up", "🩺",
         "wellness",
         [
           "free checkup", "free check-up", "free check up",
           "annual health check", "health check-up", "health checkup",
           "preventive health check", "health screening",
           "once in a year", "once a year", "yearly check",
           "complimentary check", "free annual", "checkup once",
           "health check once", "checkup in a year",
         ],
         "yearly", 1),

        ("opd", "OPD Consultation", "👨‍⚕️", "consultation",
         ["opd benefit", "outpatient", "out-patient",
          "doctor visit", "consultation benefit",
          "teleconsult", "tele consult"],
         "yearly", None),

        ("ambulance", "Ambulance Cover", "🚑", "emergency",
         ["ambulance", "emergency vehicle", "emergency transport"],
         "per_claim", None),

        ("dental", "Dental Check-up", "🦷", "wellness",
         ["dental", "oral health", "teeth check"],
         "yearly", 1),

        ("eye_checkup", "Eye Check-up", "👁️", "wellness",
         ["eye check", "vision test", "ophthalmol",
          "spectacle", "eye care"],
         "yearly", 1),

        ("wellness_bonus", "No Claim Bonus / Wellness Reward", "🎁",
         "bonus",
         ["no claim bonus", "ncb", "cumulative bonus",
          "wellness reward", "loyalty bonus", "renewal benefit",
          "bonus sum insured"],
         "yearly", None),

        ("maternity", "Maternity Benefit", "🤱", "maternity",
         ["maternity", "delivery", "new born", "newborn",
          "pre-natal", "postnatal", "prenatal"],
         "lifetime", 2),

        ("vaccination", "Vaccination", "💉", "wellness",
         ["vaccination", "vaccine", "immunization", "immunisation"],
         "yearly", None),

        ("physiotherapy", "Physiotherapy", "🏃", "wellness",
         ["physiotherapy", "physio", "rehabilitation",
          "physical therapy"],
         "yearly", None),

        ("second_opinion", "Second Medical Opinion", "📋",
         "consultation",
         ["second opinion", "expert opinion", "specialist opinion"],
         "yearly", 1),

        ("mental_health", "Mental Health Support", "🧠", "wellness",
         ["mental health", "psychiatr", "psycholog",
          "counselling", "counseling"],
         "yearly", None),

        ("ayush", "AYUSH / Alternative Medicine", "🌿", "wellness",
         ["ayush", "ayurveda", "homeopathy", "unani",
          "naturopathy", "siddha"],
         "yearly", None),

        ("home_nursing", "Home Nursing / Domiciliary", "🏠",
         "homecare",
         ["home nursing", "domiciliary", "home care",
          "home treatment", "home hospitalization"],
         "yearly", None),

        ("organ_donor", "Organ Donor Expenses", "❤️", "surgical",
         ["organ donor", "donor expense", "organ transplant benefit"],
         "lifetime", None),

        ("bariatric", "Bariatric / Weight Loss Surgery", "⚖️",
         "surgical",
         ["bariatric", "weight loss surgery", "obesity surgery"],
         "lifetime", 1),
    ]

    for (bid, label, icon, category,
         keywords, frequency, default_total) in BENEFITS:

        match_idx = -1
        matched_keyword = ""

        # Search for any keyword
        for kw in keywords:
            idx = text_lower.find(kw)
            if idx != -1:
                # Check it is NOT in an exclusion sentence
                surrounding = text_lower[max(0, idx-100):idx+150]
                exclusion_words = [
                    "not covered", "excluded", "not eligible",
                    "does not include", "not payable",
                    "not admissible", "not applicable"
                ]
                if any(ew in surrounding for ew in exclusion_words):
                    continue
                match_idx = idx
                matched_keyword = kw
                break

        if match_idx == -1:
            continue

        # Get context around match
        context = text_lower[max(0, match_idx-80):match_idx+200]

        # Try to extract count
        total = default_total
        count_patterns = [
            (r'\bonce\b', 1),
            (r'\btwice\b', 2),
            (r'(\d+)\s*times', None),
            (r'(?:upto?|maximum|max\.?)\s*(\d+)\s*'
             r'(?:times?|visits?|sessions?)', None),
            (r'(\d+)\s*(?:free\s+)?(?:visits?|sessions?|'
             r'consultations?)', None),
            (r'(\d+)\s*(?:per year|per annum|p\.a\.|annually)',
             None),
        ]
        for cp, fixed_val in count_patterns:
            cm = re.search(cp, context)
            if cm:
                if fixed_val is not None:
                    total = fixed_val
                elif cm.lastindex and cm.group(1):
                    total = int(cm.group(1))
                break

        # Try to extract monetary value
        value = None
        val_patterns = [
            r'(?:rs\.?|inr|₹)\s*([\d,]+)',
            r'([\d,]+)\s*(?:rs\.?|inr|₹)',
            r'(?:upto?|maximum|max)\s*(?:rs\.?|₹)?\s*([\d,]+)',
        ]
        for vp in val_patterns:
            vm = re.search(vp, context)
            if vm:
                try:
                    value = int(vm.group(1).replace(",", ""))
                    # Sanity check — ignore tiny/huge values
                    if value < 100 or value > 10000000:
                        value = None
                except:
                    pass
                if value:
                    break

        # Extract renewal month if mentioned (e.g. "on MARCH")
        month_names = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november",
            "december", "jan", "feb", "mar", "apr", "jun", "jul",
            "aug", "sep", "oct", "nov", "dec"
        ]
        renewal_month = None
        for month in month_names:
            if month in context:
                renewal_month = month.title()
                break

        found.append({
            "id": bid,
            "label": label,
            "icon": icon,
            "category": category,
            "frequency": frequency,
            "total_per_cycle": total,
            "value_inr": value,
            "used": 0,
            "remaining": total,
            "status": "available",
            "matched_keyword": matched_keyword,
            "renewal_month": renewal_month,
            "renewal_note": f"Renews every {renewal_month}" if renewal_month else "Renews annually with policy",
            "context_snippet": context[:100].strip(),
        })

    # ── DEDUPLICATION ─────────────────────────────────────────
    # Remove duplicate benefits by:
    # 1. Same id (exact duplicate)
    # 2. Same label (different id, same display text)
    # 3. Same category + same total (likely same benefit)

    seen_ids = set()
    seen_labels = set()
    deduped = []

    for freebie in found:
        fid = freebie["id"]
        flabel = freebie["label"].lower().strip()

        # Skip if exact id already seen
        if fid in seen_ids:
            continue

        # Skip if very similar label already seen
        # Normalize: remove "free", "annual", spaces for comparison
        normalized = (flabel
                      .replace("free", "")
                      .replace("annual", "")
                      .replace("yearly", "")
                      .replace("health", "")
                      .replace("check-up", "checkup")
                      .replace(" ", "")
                      .strip())

        if normalized in seen_labels:
            continue

        seen_ids.add(fid)
        seen_labels.add(normalized)
        deduped.append(freebie)

    return deduped

