"""
DeepSeek-based analysis path.

DeepSeek's API is OpenAI-compatible but, unlike Anthropic's, has no
hosted web_search tool. To compensate, this module runs a manual
three-step research loop:

  1. Ask DeepSeek to read the RSS digest and propose candidate topics,
     each with 1-2 search queries that would help research it further.
  2. Run those queries through Tavily (src/search_tavily.py) and collect
     snippets + URLs. If TAVILY_API_KEY isn't set, this step is skipped
     and the pipeline relies on the RSS digest + DeepSeek's own training
     knowledge only — fine for stable doctrinal topics, weaker for very
     recent developments.
  3. Ask DeepSeek again, now with the RSS digest AND the search results,
     to produce the final structured comparison — same JSON schema the
     Anthropic path uses, so build_html.py doesn't care which provider
     generated the data.

Requires:
  DEEPSEEK_API_KEY  - from https://platform.deepseek.com
  TAVILY_API_KEY    - optional, from https://tavily.com
"""
import json
import os
import re

from openai import OpenAI  # DeepSeek's API speaks the OpenAI protocol

from search_tavily import web_search

DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
MAX_TOPICS = int(os.environ.get("MAX_TOPICS", "6"))

STAGE1_SYSTEM = """You are a comparative scholar of international economic law (IEL) and \
international investment law (IIL), trained in both mainstream/Western-institutionalist and \
Global South/TWAIL traditions.

Given an RSS digest of recent IEL/IIL-adjacent posts, propose the {n} most significant CURRENT \
topics worth covering. For each, give 1-2 short web search queries that would help verify or \
extend what the digest already shows.

Output ONLY valid JSON, no markdown fences:
{{"topics": [{{"title": "...", "queries": ["...", "..."]}}]}}
"""

STAGE2_SYSTEM = """You are a comparative scholar of international economic law (IEL) and \
international investment law (IIL), trained in both mainstream/Western-institutionalist and \
Global South / TWAIL (Third World Approaches to International Law) traditions.

You are given an RSS digest and a set of web search results gathered for specific topics. \
Using ONLY this material (do not rely on internal/training knowledge for anything time-sensitive \
— if the provided material doesn't cover a detail, leave it out rather than guessing), produce \
a comparison for each topic:

1. framing: what is actually happening (2-3 neutral sentences).
2. mainstream_view: the strongest, most accurate version of how establishment scholarship, \
   OECD-country governments, and institutions like the WTO/ICSID secretariat would frame it.
3. global_south_view: the strongest, most accurate version of how critical/TWAIL scholars, \
   developing-country negotiators, or South-based institutions would frame the same issue.
4. convergence_score: 1 (sharply opposed) to 5 (largely converging), with a one-sentence \
   convergence_note.

Rules:
- Steelman both sides. Don't editorialize about who's right.
- Never invent a source — only cite URLs that actually appear in the material you were given.
- Paraphrase everything; don't quote sources for more than a few words.
- If a topic has no real mainstream/Global South fault line, drop it.

Output ONLY a single valid JSON object, no markdown fences:
{{
  "topics": [
    {{
      "title": "...",
      "framing": "...",
      "mainstream_view": "...",
      "global_south_view": "...",
      "convergence_score": 1-5,
      "convergence_note": "...",
      "mainstream_sources": [{{"title": "...", "url": "..."}}],
      "global_south_sources": [{{"title": "...", "url": "..."}}]
    }}
  ]
}}
"""


def _client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _build_digest_block(items: list[dict]) -> str:
    if not items:
        return "(No recent RSS items were retrieved this run.)"
    lines = []
    for it in items[:80]:
        lines.append(
            f"- [{it['tradition']}] {it['source']}: \"{it['title']}\" "
            f"({it['published']}) {it['link']}"
        )
    return "\n".join(lines)


def run_analysis(items: list[dict]) -> dict:
    client = _client()
    digest_block = _build_digest_block(items)

    # Stage 1: propose topics + search queries
    stage1_resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": STAGE1_SYSTEM.format(n=MAX_TOPICS)},
            {"role": "user", "content": f"RSS digest:\n{digest_block}"},
        ],
    )
    stage1 = _extract_json(stage1_resp.choices[0].message.content)

    # Stage 2: run the proposed queries through Tavily (if configured)
    research_blocks = []
    for topic in stage1.get("topics", []):
        title = topic.get("title", "")
        snippets = []
        for q in topic.get("queries", [])[:2]:
            for r in web_search(q, max_results=4):
                snippets.append(f"  - {r['title']} ({r['url']}): {r['content']}")
        block = f"Topic: {title}\n" + ("\n".join(snippets) if snippets else "  (no search results)")
        research_blocks.append(block)

    research_text = (
        "\n\n".join(research_blocks)
        if research_blocks
        else "(no search performed — TAVILY_API_KEY not set, relying on RSS digest only)"
    )

    # Stage 3: final structured comparison
    stage3_resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": STAGE2_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"RSS digest:\n{digest_block}\n\n"
                    f"Research notes:\n{research_text}\n\n"
                    "Produce the final JSON now."
                ),
            },
        ],
    )
    return _extract_json(stage3_resp.choices[0].message.content)


if __name__ == "__main__":
    from fetch_feeds import fetch_recent_items, load_config

    cfg = load_config()
    rss_items = fetch_recent_items(cfg["feeds"], cfg.get("lookback_days", 7))
    result = run_analysis(rss_items)
    print(json.dumps(result, indent=2)[:2000])
