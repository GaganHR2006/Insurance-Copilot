"""
risk_engine.py — RiskScoreEngine: Calculates a risk/quality score for an insurance policy.
Pure Python scoring logic — no LLM calls needed.
"""


class RiskScoreEngine:
    """
    Calculates a composite risk score for an insurance policy.

    Each of the four dimensions (waiting period, hospital network size,
    treatment coverage, and room-rent cap) is scored out of 25, giving a
    maximum total of 100.

    Grades:
        >= 80  → Excellent
        >= 60  → Good
        >= 40  → Fair
        <  40  → Poor
    """

    # ------------------------------------------------------------------
    @staticmethod
    def _score_waiting_period(days: int) -> int:
        """Return 25/15/5 based on waiting-period length in days."""
        if days <= 30:
            return 25
        elif days <= 90:
            return 15
        return 5

    @staticmethod
    def _score_hospital_network(size: int) -> int:
        """Return 25/15/5 based on network hospital count."""
        if size >= 100:
            return 25
        elif size >= 20:
            return 15
        return 5

    @staticmethod
    def _score_treatment_coverage(percent: int) -> int:
        """Return a score proportional to treatment coverage percentage."""
        return int((percent / 100) * 25)

    @staticmethod
    def _score_room_rent(cap: int) -> int:
        """Return 25/15/5 based on daily room-rent cap in Rs."""
        if cap >= 5000:
            return 25
        elif cap >= 3000:
            return 15
        return 5

    @staticmethod
    def _grade(total: int) -> str:
        """Return a letter grade for the given total score."""
        if total >= 80:
            return "Excellent"
        elif total >= 60:
            return "Good"
        elif total >= 40:
            return "Fair"
        return "Poor"

    @staticmethod
    def _recommendation(grade: str) -> str:
        """Return a short advisory message based on the grade."""
        messages = {
            "Excellent": "This policy offers outstanding coverage. Highly recommended.",
            "Good": "A solid policy with good coverage. Minor gaps exist — review exclusions.",
            "Fair": "Average coverage. Consider supplemental plans for critical treatments.",
            "Poor": "Limited coverage. Look for policies with better networks and higher caps.",
        }
        return messages.get(grade, "Review policy terms carefully.")

    # ------------------------------------------------------------------
    def calculate(self, policy_data: dict) -> dict:
        """
        Calculate the risk/quality score for a policy.

        Args:
            policy_data: A dict with these integer keys:
                - waiting_period_days      : waiting period in days
                - hospital_network_size    : number of network hospitals
                - treatment_coverage_percent: coverage % (0–100)
                - room_rent_cap            : daily room-rent cap in Rs.

        Returns:
            A dict with keys:
                - total_score  (int)
                - grade        (str)
                - breakdown    (dict of component scores)
                - recommendation (str)
        """
        try:
            wp_score = self._score_waiting_period(
                int(policy_data.get("waiting_period_days", 90))
            )
            hn_score = self._score_hospital_network(
                int(policy_data.get("hospital_network_size", 0))
            )
            tc_score = self._score_treatment_coverage(
                int(policy_data.get("treatment_coverage_percent", 0))
            )
            rr_score = self._score_room_rent(
                int(policy_data.get("room_rent_cap", 0))
            )

            total = wp_score + hn_score + tc_score + rr_score
            grade = self._grade(total)

            return {
                "total_score": total,
                "grade": grade,
                "breakdown": {
                    "waiting_period_score": wp_score,
                    "hospital_network_score": hn_score,
                    "treatment_coverage_score": tc_score,
                    "room_rent_score": rr_score,
                },
                "recommendation": self._recommendation(grade),
            }

        except Exception as exc:
            return {
                "total_score": 0,
                "grade": "Unknown",
                "breakdown": {},
                "recommendation": f"[ERROR] Could not calculate score: {exc}",
            }
