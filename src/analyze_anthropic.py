"""
Turns a list of RSS items into a structured Western-mainstream vs.
Global South / TWAIL comparison, using the Anthropic API with the
hosted web_search tool to verify and fill gaps the RSS feeds missed.
"""
import json
import os
import re

from anthropic import Anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_TOPICS = int(os.environ.get("MAX_TOPICS", "6"))

SYSTEM_PROMPT = """You are a comparative scholar of international economic law (IEL) \
and international investment law (IIL), trained in both the mainstream/Western \
institutionalist tradition (WTO law, ICSID/investment arbitration doctrine, \
liberal international law) and Global South / TWAIL (Third World Approaches to \
International Law) critical traditions.

Your job each run is to identify the most significant CURRENT topics in IEL/IIL \
and, for each one, lay out:
1. What is actually happening (neutral framing, 2-3 sentences).
2. The mainstream / Western-institutionalist reading of it — the strongest, most \
   accurate version of how establishment scholarship, OECD-country governments, \
   and institutions like the WTO/ICSID secretariat would frame the issue.
3. The Global South / TWAIL reading of the same issue — the strongest, most \
   accurate version of how critical scholars, developing-country negotiators, or \
   South-based institutions (South Centre, AfronomicsLaw, TWN) would frame it.
4. A convergence score from 1 (sharply opposed, no shared premises) to 5 \
   (largely converging, disagreement is about implementation only), with a \
   one-sentence rationale.

Rules:
- Use web search to verify facts and fill in detail the RSS items don't cover. \
  Do not rely on memory alone for anything time-sensitive (case outcomes, treaty \
  text, current negotiating positions).
- Never invent a source. Every source you cite must be one you actually found via \
  search or that was given to you in the RSS digest.
- Paraphrase everything. Do not quote any source for more than a few words.
- Steelman both sides. Do not editorialize about which side is "right" — the \
  reader is a law professor who wants the strongest version of each position, \
  not a verdict.
- If a topic genuinely has no meaningful Global South/mainstream split (it's a \
  purely technical or procedural matter), skip it and pick a topic that does \
  have a real fault line.
- Output ONLY a single valid JSON object. No markdown fences, no commentary \
  before or after it.

JSON schema:
{
  "topics": [
    {
      "title": "short topic title",
      "framing": "2-3 sentence neutral description of what's happening",
      "mainstream_view": "1-2 paragraphs",
      "global_south_view": "1-2 paragraphs",
      "convergence_score": 1-5,
      "convergence_note": "one sentence",
      "mainstream_sources": [{"title": "...", "url": "..."}],
      "global_south_sources": [{"title": "...", "url": "..."}]
    }
  ]
}
"""


def _build_digest_block(items: list[dict]) -> str:
    if not items:
        return "(No recent RSS items were retrieved this run — rely on web search.)"
    lines = []
    for it in items[:80]:  # keep prompt bounded
        lines.append(
            f"- [{it['tradition']}] {it['source']}: \"{it['title']}\" "
            f"({it['published']}) {it['link']}"
        )
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    text = text.strip()
    # Strip accidental markdown fences if the model adds them anyway.
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fall back to grabbing the largest {...} block in the text.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def run_analysis(items: list[dict]) -> dict:
    client = Anthropic()  # reads ANTHROPIC_API_KEY from env
    digest_block = _build_digest_block(items)

    user_msg = f"""Recent RSS digest items from the last lookback window:

{digest_block}

Using these as a starting point, plus web search for verification and to fill \
gaps, identify the {MAX_TOPICS} most significant CURRENT topics/issues in \
international economic law and international investment law. Produce the \
comparison for each as instructed in your system prompt. Output strict JSON only."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": user_msg}],
    )

    text_blocks = [block.text for block in response.content if block.type == "text"]
    full_text = "\n".join(text_blocks)
    return _extract_json(full_text)


if __name__ == "__main__":
    # Quick manual smoke test: python src/analyze.py
    from fetch_feeds import fetch_recent_items, load_config

    cfg = load_config()
    rss_items = fetch_recent_items(cfg["feeds"], cfg.get("lookback_days", 7))
    result = run_analysis(rss_items)
    print(json.dumps(result, indent=2)[:2000])
