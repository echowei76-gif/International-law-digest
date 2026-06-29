"""Pull recent items from the configured RSS feeds."""
import datetime
from typing import Any

import feedparser
import yaml
from dateutil import parser as dateparser


def load_config(config_path: str = "config/feeds.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_published(entry: dict) -> datetime.datetime | None:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        dt = dateparser.parse(raw)
    except (ValueError, OverflowError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def fetch_recent_items(feeds: list[dict], lookback_days: int = 7) -> list[dict[str, Any]]:
    """Return a flat list of {source, tradition, title, link, published, summary} dicts."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=lookback_days)
    items: list[dict[str, Any]] = []

    for feed in feeds:
        try:
            parsed = feedparser.parse(feed["url"])
        except Exception as exc:  # noqa: BLE001 - feed sources are unpredictable
            print(f"[warn] could not fetch {feed['name']}: {exc}")
            continue

        if getattr(parsed, "bozo", False) and not parsed.entries:
            print(f"[warn] {feed['name']} returned no usable entries ({parsed.bozo_exception})")
            continue

        for entry in parsed.entries:
            pub_dt = _parse_published(entry)
            if pub_dt is not None and pub_dt < cutoff:
                continue  # too old, skip
            items.append(
                {
                    "source": feed["name"],
                    "tradition": feed.get("tradition", "unknown"),
                    "title": entry.get("title", "Untitled"),
                    "link": entry.get("link", ""),
                    "published": pub_dt.isoformat() if pub_dt else "unknown",
                    "summary": (entry.get("summary", "") or "")[:400],
                }
            )

    items.sort(key=lambda i: i["published"], reverse=True)
    return items


if __name__ == "__main__":
    cfg = load_config()
    found = fetch_recent_items(cfg["feeds"], cfg.get("lookback_days", 7))
    print(f"Fetched {len(found)} items")
    for it in found[:20]:
        print(f"- [{it['tradition']}] {it['source']}: {it['title']}")
