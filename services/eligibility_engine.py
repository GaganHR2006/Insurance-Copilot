"""
Eligibility Engine — Checks treatment eligibility using PDF policy as
PRIMARY source of truth, falling back to the JSON dataset.
"""

from typing import Optional

from services.data_loader import load_policies, load_treatments, get_pdf_policy


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def treatment_in_list(treatment: str, treatment_list: list) -> bool:
    """Flexible treatment matching: exact, partial, word-level."""
    t_norm = normalize(treatment)
    for item in treatment_list:
        i_norm = normalize(str(item))
        if t_norm == i_norm:
            return True
        if t_norm in i_norm or i_norm in t_norm:
            return True
        if set(t_norm.split()) & set(i_norm.split()):
            return True
    return False


def get_treatment_details(treatment: str) -> Optional[dict]:
    """Find treatment record from treatments.json."""
    treatments = load_treatments()
    t_norm = normalize(treatment)
    for t in treatments:
        name = normalize(str(t.get("name") or t.get("treatment_name") or ""))
        if t_norm == name or t_norm in name or name in t_norm:
            return t
    return None


def get_policy_details(policy_name: str) -> Optional[dict]:
    """Find policy record from policies.json."""
    policies = load_policies()
    p_norm = normalize(policy_name)
    for p in policies:
        name     = normalize(str(p.get("name") or p.get("policy_name") or ""))
        provider = normalize(str(p.get("provider") or ""))
        if p_norm in name or p_norm in provider or name in p_norm:
            return p
    return None


def check_eligibility(
    treatment: str,
    policy: str,
    age: int,
    waiting_period_served_days: int,
) -> dict:
    """
    Core eligibility check.
    PDF policy data always overrides the JSON dataset.
    """
    pdf = get_pdf_policy()
    pdf_uploaded = bool(pdf)

    # ── SOURCE 1: Uploaded PDF ────────────────────────────────────────────────
    pdf_insurer     = pdf.get("insurer")
    pdf_covered     = pdf.get("covered_treatments", [])
    pdf_exclusions  = pdf.get("exclusions", [])
    pdf_waiting     = pdf.get("waiting_period_days")
    pdf_sum_insured = pdf.get("sum_insured")
    pdf_room_rent   = pdf.get("room_rent_cap")
    pdf_policy_name = pdf.get("policy_name")
    pdf_sub_limits  = pdf.get("sub_limits", {})
    pdf_min_age     = pdf.get("min_age", 18)
    pdf_max_age     = pdf.get("max_age", 65)

    # ── SOURCE 2: Dataset ─────────────────────────────────────────────────────
    effective_policy = policy or pdf_insurer or "Unknown"
    db_policy        = get_policy_details(effective_policy)
    treatment_record = get_treatment_details(treatment)

    # ── Merge: PDF wins over dataset ─────────────────────────────────────────
    if pdf_covered:
        covered_treatments = pdf_covered
        coverage_source    = "your uploaded policy PDF"
    elif db_policy:
        covered_treatments = db_policy.get("covered_treatments", [])
        coverage_source    = "our policy database"
    else:
        covered_treatments = []
        coverage_source    = "no data source found"

    if pdf_exclusions:
        exclusions = pdf_exclusions
    elif db_policy:
        exclusions = db_policy.get("exclusions", [])
    else:
        exclusions = []

    if pdf_waiting is not None:
        required_waiting = int(pdf_waiting)
        waiting_source   = "your uploaded PDF"
    elif db_policy and db_policy.get("waiting_period_days"):
        required_waiting = int(db_policy["waiting_period_days"])
        waiting_source   = "policy database"
    elif treatment_record and treatment_record.get("waiting_period_days"):
        required_waiting = int(treatment_record["waiting_period_days"])
        waiting_source   = "treatment-specific data"
    else:
        required_waiting = 90
        waiting_source   = "default estimate"

    if pdf_sum_insured:
        sum_insured = int(str(pdf_sum_insured).replace(",", ""))
    elif db_policy and db_policy.get("sum_insured"):
        sum_insured = int(str(db_policy["sum_insured"]).replace(",", ""))
    else:
        sum_insured = 500000

    if treatment_record:
        avg_cost          = treatment_record.get("avg_cost_inr", 0)
        pre_auth_required = treatment_record.get("pre_auth_required", False)
        risk_level        = treatment_record.get("risk_level", "medium")
        common_exclusions = treatment_record.get("common_exclusions", [])
    else:
        avg_cost = pre_auth_required = 0
        risk_level        = "unknown"
        common_exclusions = []
        pre_auth_required = False

    min_age = int(pdf_min_age)
    max_age = int(pdf_max_age)

    # ── Individual checks ─────────────────────────────────────────────────────
    is_covered         = treatment_in_list(treatment, covered_treatments)
    is_excluded        = treatment_in_list(treatment, exclusions) or \
                         treatment_in_list(treatment, common_exclusions)
    not_excluded       = not is_excluded
    waiting_period_met = waiting_period_served_days >= required_waiting
    waiting_gap        = max(0, required_waiting - waiting_period_served_days)
    age_eligible       = min_age <= age <= max_age
    sum_sufficient     = sum_insured >= avg_cost * 0.5 if avg_cost > 0 else True

    eligible = is_covered and not_excluded and waiting_period_met and age_eligible

    # ── Estimated coverage ────────────────────────────────────────────────────
    coverage = coverage_note = None
    if eligible and avg_cost > 0:
        t_norm    = normalize(treatment)
        sub_limit = None
        for key, val in pdf_sub_limits.items():
            if normalize(key) in t_norm:
                sub_limit = int(str(val).replace(",", ""))
                break
        raw_coverage = int(avg_cost * 0.85)
        if sub_limit:
            coverage      = min(raw_coverage, sub_limit)
            coverage_note = f"Sub-limit of ₹{sub_limit:,} applies"
        else:
            coverage      = raw_coverage
            coverage_note = "Standard 85% coverage estimate"

    # ── Reason string ─────────────────────────────────────────────────────────
    if eligible:
        reason = (
            f"All checks passed. {treatment.title()} is covered under "
            f"{pdf_policy_name or effective_policy}."
        )
    else:
        failed = []
        if not is_covered:
            sample = ", ".join(covered_treatments[:5]) or "none found"
            failed.append(
                f"'{treatment}' is not listed in {coverage_source}. "
                f"Covered: {sample}"
            )
        if is_excluded:
            failed.append(f"'{treatment}' is explicitly excluded in your policy")
        if not waiting_period_met:
            failed.append(
                f"Waiting period not met — need {required_waiting} days "
                f"({waiting_source}), served {waiting_period_served_days}. "
                f"{waiting_gap} more days needed."
            )
        if not age_eligible:
            failed.append(
                f"Age {age} outside eligible range ({min_age}–{max_age})"
            )
        reason = " | ".join(failed)

    # ── Warnings ──────────────────────────────────────────────────────────────
    warnings = []
    if pre_auth_required and eligible:
        warnings.append(
            "Pre-authorization is mandatory before this treatment. "
            "Claim will be rejected without it."
        )
    if not sum_sufficient and avg_cost > 0:
        warnings.append(
            f"Your sum insured (₹{sum_insured:,}) may not fully cover "
            f"estimated cost ₹{avg_cost:,}. Out-of-pocket expenses likely."
        )
    if pdf_room_rent and eligible:
        try:
            warnings.append(
                f"Room rent capped at ₹{int(pdf_room_rent):,}/day. "
                f"Choosing a higher room will proportionally reduce all claims."
            )
        except (ValueError, TypeError):
            pass

    return {
        "eligible": eligible,
        "treatment": treatment,
        "policy_used": pdf_policy_name or effective_policy,
        "data_source": {
            "pdf_uploaded":        pdf_uploaded,
            "insurer_from_pdf":    pdf_insurer,
            "coverage_source":     coverage_source,
            "waiting_period_source": waiting_source,
        },
        "checks": {
            "treatment_covered": {
                "passed": is_covered,
                "detail": (
                    f"Found in {coverage_source}"
                    if is_covered else
                    f"Not found in {coverage_source}. "
                    f"Covered: {', '.join(covered_treatments[:5]) or 'none'}"
                ),
            },
            "not_excluded": {
                "passed": not_excluded,
                "detail": (
                    "Not in exclusion list"
                    if not_excluded else
                    "Explicitly excluded in policy"
                ),
            },
            "waiting_period_met": {
                "passed":       waiting_period_met,
                "required_days": required_waiting,
                "served_days":   waiting_period_served_days,
                "gap_days":      waiting_gap,
                "detail": (
                    f"Waiting period satisfied ({waiting_period_served_days}/{required_waiting} days)"
                    if waiting_period_met else
                    f"Need {waiting_gap} more days (Required: {required_waiting} from {waiting_source})"
                ),
            },
            "age_eligible": {
                "passed": age_eligible,
                "detail": (
                    f"Age {age} is within eligible range ({min_age}–{max_age})"
                    if age_eligible else
                    f"Age {age} outside eligible range ({min_age}–{max_age})"
                ),
            },
            "sum_insured_sufficient": {
                "passed":         sum_sufficient,
                "sum_insured":    sum_insured,
                "estimated_cost": avg_cost,
                "detail": (
                    f"Sum insured ₹{sum_insured:,} covers estimate ₹{avg_cost:,}"
                    if sum_sufficient else
                    f"Sum insured ₹{sum_insured:,} may be insufficient for ₹{avg_cost:,}"
                ),
            },
        },
        "reason":                  reason,
        "warnings":                warnings,
        "estimated_coverage_inr":  coverage,
        "coverage_note":           coverage_note,
        "treatment_info": {
            "avg_cost_inr":    avg_cost,
            "pre_auth_required": pre_auth_required,
            "risk_level":      risk_level,
        },
        "policy_info": {
            "sum_insured":        sum_insured,
            "room_rent_cap":      pdf_room_rent,
            "waiting_period_days": required_waiting,
        },
    }
