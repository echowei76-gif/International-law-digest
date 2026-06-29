"""Orchestrates the full pipeline: fetch -> analyze -> render -> write."""
import datetime
import json
import os

from analyze import run_analysis
from build_html import render_html
from fetch_feeds import fetch_recent_items, load_config

STATE_PATH = "data/state.json"


def next_issue_number(state_path: str = STATE_PATH) -> int:
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {"issue": 0}
    state["issue"] += 1
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    return state["issue"]


def main() -> None:
    cfg = load_config()
    lookback_days = int(os.environ.get("LOOKBACK_DAYS", cfg.get("lookback_days", 7)))

    print(f"Fetching {len(cfg['feeds'])} feeds (lookback {lookback_days}d)...")
    items = fetch_recent_items(cfg["feeds"], lookback_days)
    print(f"Got {len(items)} recent RSS items.")

    print("Running comparative analysis (this calls the Anthropic API with web search)...")
    analysis = run_analysis(items)
    print(f"Analysis returned {len(analysis.get('topics', []))} topics.")

    issue_no = next_issue_number()
    issue_date = datetime.date.today().isoformat()

    html = render_html(analysis, issue_no, issue_date)

    os.makedirs("docs/archive", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    archive_path = f"docs/archive/{issue_date}-issue-{issue_no}.html"
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Keep the raw JSON too, in case you want to reuse the data elsewhere
    # (a dashboard, a newsletter, a feed of your own).
    with open(f"data/issue-{issue_no}.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    print(f"Wrote docs/index.html and {archive_path}")


if __name__ == "__main__":
    main()
