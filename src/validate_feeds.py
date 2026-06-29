"""
Run this once from a machine with real internet access (not this sandbox)
to sanity-check every feed in config/feeds.yaml before you wire the repo
into GitHub Actions.

    python src/validate_feeds.py

It will not raise on a broken feed — it prints a pass/fail report so you
can fix config/feeds.yaml in one pass instead of debugging blank digest
issues later.
"""
import sys
import yaml
import feedparser


def main(config_path: str = "config/feeds.yaml") -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        feeds = yaml.safe_load(f)["feeds"]

    ok, broken = [], []
    for feed in feeds:
        parsed = feedparser.parse(feed["url"])
        entry_count = len(parsed.entries)
        if parsed.bozo and entry_count == 0:
            broken.append(feed)
            print(f"[FAIL] {feed['name']:<35} {feed['url']}  -> {parsed.bozo_exception}")
        elif entry_count == 0:
            broken.append(feed)
            print(f"[WARN] {feed['name']:<35} {feed['url']}  -> parsed OK but 0 entries")
        else:
            ok.append(feed)
            latest = parsed.entries[0].get("title", "?")
            print(f"[ OK ] {feed['name']:<35} {entry_count} entries, latest: {latest[:60]}")

    print(f"\n{len(ok)} feeds OK, {len(broken)} need attention.")
    if broken:
        sys.exit(1)


if __name__ == "__main__":
    main()
