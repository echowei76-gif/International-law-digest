"""
Minimal Tavily search client. Used only by the DeepSeek analysis path,
since DeepSeek's API (unlike Anthropic's) has no built-in hosted
web-search tool.

Get a free key (1,000 searches/month on the free tier as of writing) at
https://tavily.com. If TAVILY_API_KEY is not set, web_search() just
returns an empty list and the pipeline falls back to RSS-only analysis.
"""
import os

import requests

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
TAVILY_URL = "https://api.tavily.com/search"


def web_search(query: str, max_results: int = 4) -> list[dict]:
    if not TAVILY_API_KEY:
        return []
    try:
        resp = requests.post(
            TAVILY_URL,
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        print(f"[warn] Tavily search failed for '{query}': {exc}")
        return []

    return [
        {
            "title": r.get("title", "Untitled"),
            "url": r.get("url", ""),
            "content": (r.get("content", "") or "")[:500],
        }
        for r in data.get("results", [])
    ]
