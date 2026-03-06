"""
AI Engine Service - Handles all communication with Groq AI via OpenAI-compatible API.
Automatically injects local hospital/policy/treatment data as context for accurate answers.
"""

import json
import os

import httpx
from dotenv import load_dotenv

from services.data_loader import load_hospitals, load_policies, load_treatments

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")


def _build_system_prompt() -> str:
    """Build a system prompt that includes structured data from local JSON files."""
    try:
        hospitals  = load_hospitals()
        policies   = load_policies()
        treatments = load_treatments()

        # Compact summaries — enough for the AI to give accurate answers
        hospital_summary = "\\n".join(
            f"- {h['name']} ({h['city']}): treatments={', '.join(h.get('treatments', []))}, "
            f"network_policies={', '.join(h.get('network_policies', []))}, "
            f"icu_beds={h.get('icu_beds', 'N/A')}, general_beds={h.get('general_beds', 'N/A')}, "
            f"rating={h.get('rating', 'N/A')}"
            for h in hospitals
        )

        def _fmt_currency(val) -> str:
            return f"₹{val:,}" if isinstance(val, (int, float)) else "N/A"

        policy_summary = "\\n".join(
            f"- {p['name']} ({p.get('provider', 'Unknown')}): "
            f"sum_insured={_fmt_currency(p.get('sum_insured_inr'))}, "
            f"waiting_period={p.get('waiting_period_days', 'N/A')} days, "
            f"room_rent_cap={'None' if p.get('room_rent_cap') is None else _fmt_currency(p.get('room_rent_cap'))}/day, "
            f"covered={', '.join(p.get('covered_treatments', [])[:5])}, "
            f"exclusions={', '.join(p.get('exclusions', [])[:4])}"
            for p in policies
        )

        treatment_summary = "\\n".join(
            f"- {t['name']}: avg_cost={_fmt_currency(t.get('avg_cost_inr'))}, "
            f"risk={t.get('risk_level', 'N/A')}, "
            f"pre_auth={t.get('pre_auth_required', False)}, "
            f"category={t.get('category', 'N/A')}"
            for t in treatments
        )

        data_context = (
            f"HOSPITALS IN OUR NETWORK:\\n{hospital_summary}\\n\\n"
            f"INSURANCE POLICIES WE SUPPORT:\\n{policy_summary}\\n\\n"
            f"TREATMENTS & COSTS:\\n{treatment_summary}"
        )
    except Exception as e:
        print(f"Error building system prompt: {e}")
        data_context = "Note: Local data unavailable, answer from general knowledge."

    strict_rules = (
        "You are a concise Indian health insurance advisor inside Insurance Copilot.\n\n"
        "RESPONSE RULES \u2014 follow strictly, no exceptions:\n\n"
        "1. LENGTH: Maximum 5 bullet points per response. No more.\n"
        "   - Each bullet = 1 short sentence (max 15 words).\n"
        "   - No paragraphs. No intro text. No closing text. Start bullets immediately.\n\n"
        "2. FORMAT: Use \"\u2022\" for every point.\n"
        "   - Bold (**text**) only the single most critical fact per response.\n"
        "   - Critical = a rupee limit, waiting period, exclusion, or rejection risk.\n\n"
        "3. DIRECTNESS: Answer only what was asked. Nothing extra.\n"
        "   - \"Is X covered?\" \u2192 Yes/No + limit + waiting period. Done.\n"
        "   - \"Loopholes?\" \u2192 Top 4 loopholes only. Done.\n"
        "   - Never explain what a bullet already says.\n"
        "   - Never add \"consult your advisor\" or disclaimer sentences.\n\n"
        "4. USE POLICY CONTEXT: If a policy PDF was uploaded, answer strictly from it.\n"
        "   - Do not add generic advice not present in the document.\n"
        "   - If something is not in the document, say \"\u2022 Not mentioned in your policy.\"\n\n"
        "---\n\n"
        "EXAMPLE \u2014 \"Is knee replacement covered?\"\n\n"
        "CORRECT (do this):\n"
        "\u2022 Knee replacement is covered under comprehensive health plans.\n"
        "\u2022 **Waiting period: 2\u20134 years before you can claim.**\n"
        "\u2022 Pre-authorization is mandatory before surgery.\n"
        "\u2022 Sub-limits on implants may cap reimbursement at \u20b91,00,000.\n"
        "\u2022 Cashless available at network hospitals only.\n\n"
        "WRONG (never do this):\n"
        "\"No, knee replacement is not mentioned as a covered treatment in the provided\n"
        "policy document. The document only lists the following treatments as covered:\n"
        "1. Cardiac surgery 2. Dialysis 3. Chemotherapy...\"\n\n"
        "---\n\n"
        "EXAMPLE \u2014 \"Loopholes in my insurance\"\n\n"
        "CORRECT (do this):\n"
        "\u2022 **Room rent capped at \u20b95,000/day \u2014 higher rooms billed proportionally.**\n"
        "\u2022 Waiting period: 30 days general, 2 years for pre-existing diseases.\n"
        "\u2022 Organ transplant, hip replacement, cardiac bypass are excluded.\n"
        "\u2022 Pre-auth required for knee replacement, chemotherapy, cardiac bypass.\n"
        "\u2022 Voluntary co-payment: \u20b90 now but may change at renewal.\n\n"
        "WRONG (never do this):\n"
        "Long numbered paragraphs mixing bold mid-sentence with explanations.\n\n"
        "---\n\n"
        "RULE SUMMARY:\n"
        "- Max 5 bullets\n"
        "- Max 15 words per bullet\n"
        "- Max 1 bold per response\n"
        "- Zero filler, zero disclaimers, zero elaboration"
    )

    return f"{strict_rules}\n\n{data_context}"


def enforce_bullet_format(text: str) -> str:
    """
    Post-processes AI response to guarantee bullet format.
    Strips any paragraph text, keeps only bullet lines.
    Enforces max 4 bullets. Ensures at least one <b> tag exists.
    """
    lines = text.strip().split("\n")
    bullets = []

    for line in lines:
        line = line.strip()
        # Accept lines starting with bullet or <b>•
        if line.startswith("•") or line.startswith("<b>•"):
            bullets.append(line)
        elif line.startswith(("<b>", "**•", "- ", "* ")):
            # Normalize alternate bullet formats
            clean = line.replace("**", "").replace("- ", "• ").replace("* ", "• ")
            if not clean.startswith("•"):
                clean = "• " + clean
            bullets.append(clean)

    # Fallback: if AI returned numbered list, convert it
    if not bullets:
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                clean = line.lstrip("0123456789.-) ").strip()
                if clean:
                    bullets.append(f"• {clean}")

    # Second fallback: pure paragraph — split into sentences and convert to bullets
    if not bullets:
        import re
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        for sent in sentences:
            sent = sent.strip().rstrip('.!?')
            if len(sent) > 10:  # Skip very short fragments
                bullets.append(f"• {sent}.")

    # Enforce max 4 bullets
    bullets = bullets[:4]

    # Ensure at least one bold bullet exists (make first one bold if none)
    has_bold = any("<b>" in b for b in bullets)
    if not has_bold and bullets:
        bullets[0] = f"<b>{bullets[0]}</b>"

    return "\n".join(bullets) if bullets else "• Unable to process response."


async def ask_ai(question: str, context: str = "") -> str:
    """
    Send a question to the AI and return a strictly-formatted bullet response.

    Uses Groq API with:
    - max_tokens=300 to physically cap response length
    - A system prompt with concrete examples using <b> tags
    - enforce_bullet_format() post-processor to strip any drifted output
    """
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY", "")
    model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

    system_prompt = _build_system_prompt()

    user_message = f"{context}\n\nQuestion: {question}" if context else question

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 300,
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
        )
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"].strip()
        return enforce_bullet_format(raw)
