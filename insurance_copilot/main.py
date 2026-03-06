"""
main.py — Insurance Copilot CLI Demo
Runs all 5 components in sequence with colorful ANSI output.
"""

import json
import os
import sys

# Reconfigure stdout/stderr to UTF-8 so box-drawing chars work on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

# ── ANSI colour helpers ────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
MAGENTA = "\033[95m"
WHITE  = "\033[97m"


def header(text: str) -> None:
    """Print a bold cyan section header."""
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}")


def sub(text: str) -> None:
    """Print a yellow sub-heading."""
    print(f"\n{YELLOW}>> {text}{RESET}")


def ok(text: str) -> None:
    """Print a green success line."""
    print(f"{GREEN}  {text}{RESET}")


def warn(text: str) -> None:
    """Print a yellow warning line."""
    print(f"{YELLOW}  [!] {text}{RESET}")


def err(text: str) -> None:
    """Print a red error line."""
    print(f"{RED}  [X] {text}{RESET}")


def dim(text: str) -> None:
    """Print dimmed white text."""
    print(f"{WHITE}  {text}{RESET}")


# ── 1. RAG Demo ───────────────────────────────────────────────────────────────
def demo_rag() -> None:
    """Demonstrate the PolicyRAG system with two questions."""
    header("[RAG] Policy Question & Answer")
    try:
        from rag_system import PolicyRAG

        rag = PolicyRAG()
        sub("Loading policy documents …")
        rag.load_documents("sample_policies")

        sub("Building FAISS vectorstore …")
        rag.build_vectorstore()

        questions = [
            "What is the waiting period for pre-existing conditions?",
            "Is LASIK surgery covered?",
        ]
        for q in questions:
            sub(f"Q: {q}")
            answer = rag.answer(q)
            ok(f"A: {answer}")
    except Exception as exc:
        err(f"RAG demo failed: {exc}")


# ── 2. Loophole Detection Demo ────────────────────────────────────────────────
def demo_loophole() -> None:
    """Read policy1.txt and pretty-print detected loopholes."""
    header("[LOOPHOLE] Detection Demo")
    try:
        from loophole_detector import LoopholeDetector

        policy_path = os.path.join("sample_policies", "policy1.txt")
        with open(policy_path, encoding="utf-8") as fh:
            policy_text = fh.read()

        sub("Analysing policy for loopholes …")
        detector = LoopholeDetector()
        result = detector.detect(policy_text)

        if "error" in result:
            warn(f"Partial result — {result['error']}")

        print(f"\n{MAGENTA}{json.dumps(result, indent=2)}{RESET}")
    except Exception as exc:
        err(f"Loophole detection demo failed: {exc}")


# ── 3. Risk Score Demo ────────────────────────────────────────────────────────
def demo_risk() -> None:
    """Calculate and display a risk score for a sample policy."""
    header("[RISK] Score Demo")
    try:
        from risk_engine import RiskScoreEngine

        engine = RiskScoreEngine()
        policy_data = {
            "waiting_period_days": 30,
            "hospital_network_size": 50,
            "treatment_coverage_percent": 80,
            "room_rent_cap": 3000,
        }
        sub("Input data:")
        for k, v in policy_data.items():
            dim(f"  {k}: {v}")

        result = engine.calculate(policy_data)

        sub("Results:")
        ok(f"Total Score   : {result['total_score']} / 100")
        ok(f"Grade         : {result['grade']}")
        ok(f"Recommendation: {result['recommendation']}")

        sub("Breakdown:")
        for component, score in result["breakdown"].items():
            dim(f"  {component:<35} {score:>3} / 25")
    except Exception as exc:
        err(f"Risk score demo failed: {exc}")


# ── 4. Precaution Advisor Demo ────────────────────────────────────────────────
def demo_precaution() -> None:
    """Show precautions for an uncovered treatment."""
    header("[ADVISOR] Precaution Advisor Demo")
    try:
        from precaution_advisor import PrecautionAdvisor

        advisor = PrecautionAdvisor()
        sub("Fetching precautions for: LASIK Eye Surgery (not covered) …")
        result = advisor.advise("LASIK Eye Surgery", is_covered=False)

        print(f"\n{BOLD}  Treatment : {result.get('treatment', 'N/A')}{RESET}")
        print(f"{BOLD}  Coverage  : {YELLOW}{result.get('coverage', 'N/A')}{RESET}")
        print(f"\n{BOLD}  Precautions:{RESET}")
        for precaution in result.get("precautions", []):
            ok(f"  • {precaution}")

        if "disclaimer" in result:
            warn(result["disclaimer"])
    except Exception as exc:
        err(f"Precaution advisor demo failed: {exc}")


# ── 5. Chat Memory Demo ───────────────────────────────────────────────────────
def demo_chat() -> None:
    """Send three messages demonstrating rolling conversation memory."""
    header("[CHAT] Memory Demo")
    messages = [
        "My policy has a 30 day waiting period. Is that good?",
        "What about room rent caps?",
        "Summarize what we discussed about my policy.",
    ]
    try:
        from chat_memory import InsuranceChatbot

        bot = InsuranceChatbot()
        for idx, msg in enumerate(messages, start=1):
            sub(f"Turn {idx} — User: {msg}")
            response = bot.chat(msg)
            ok(f"Assistant: {response}")
    except Exception as exc:
        err(f"Chat memory demo failed: {exc}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}{'  Insurance Copilot Demo  ':^60}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}")

    demo_rag()
    demo_loophole()
    demo_risk()
    demo_precaution()
    demo_chat()

    print(f"\n{BOLD}{GREEN}[OK] Demo complete!{RESET}\n")
