"""
Provider-agnostic entry point. main.py imports run_analysis from here and
never needs to know whether you're using Anthropic or DeepSeek under the
hood — set LLM_PROVIDER to pick.
"""
import os

PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()


def run_analysis(items: list[dict]) -> dict:
    if PROVIDER == "deepseek":
        from analyze_deepseek import run_analysis as _run
    elif PROVIDER == "anthropic":
        from analyze_anthropic import run_analysis as _run
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{PROVIDER}'. Use 'anthropic' or 'deepseek'."
        )
    return _run(items)


if __name__ == "__main__":
    import json

    from fetch_feeds import fetch_recent_items, load_config

    cfg = load_config()
    rss_items = fetch_recent_items(cfg["feeds"], cfg.get("lookback_days", 7))
    result = run_analysis(rss_items)
    print(json.dumps(result, indent=2)[:2000])
