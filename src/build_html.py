"""Renders the analysis JSON into a single self-contained HTML page."""
import html as html_lib

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Fault Line — Issue {issue_no}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --paper: #EDE8DC;
    --ink: #1B1B16;
    --ink-soft: #4A4640;
    --rule: #C9C1AE;
    --mainstream: #2E3A59;
    --mainstream-soft: #DDE2EC;
    --globalsouth: #9C5328;
    --globalsouth-soft: #F1DFCC;
    --gauge-empty: #D9D2C0;
  }}

  * {{ box-sizing: border-box; }}

  body {{
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: 'IBM Plex Sans', sans-serif;
    line-height: 1.55;
  }}

  .wrap {{
    max-width: 980px;
    margin: 0 auto;
    padding: 48px 24px 96px;
  }}

  header.masthead {{
    border-bottom: 3px solid var(--ink);
    padding-bottom: 18px;
    margin-bottom: 36px;
  }}

  .masthead-row {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 8px;
  }}

  .masthead-title {{
    font-family: 'Source Serif 4', serif;
    font-weight: 700;
    font-size: 42px;
    letter-spacing: -0.01em;
    margin: 0;
  }}

  .masthead-meta {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    color: var(--ink-soft);
    text-align: right;
    white-space: nowrap;
  }}

  .masthead-sub {{
    font-size: 14px;
    color: var(--ink-soft);
    margin-top: 6px;
    max-width: 640px;
  }}

  .legend {{
    display: flex;
    gap: 24px;
    margin: 24px 0 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .legend span {{ display: flex; align-items: center; gap: 8px; }}
  .swatch {{ width: 10px; height: 10px; display: inline-block; }}

  .topic {{
    margin-top: 56px;
  }}

  .topic-head {{
    display: flex;
    align-items: baseline;
    gap: 14px;
    margin-bottom: 10px;
  }}

  .topic-no {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    color: var(--ink-soft);
    white-space: nowrap;
  }}

  .topic-title {{
    font-family: 'Source Serif 4', serif;
    font-weight: 600;
    font-size: 26px;
    margin: 0;
  }}

  .framing {{
    color: var(--ink-soft);
    font-size: 15px;
    max-width: 760px;
    margin-bottom: 22px;
  }}

  .split {{
    display: grid;
    grid-template-columns: 1fr 2px 1fr;
    gap: 0;
    border-top: 1px solid var(--rule);
    border-bottom: 1px solid var(--rule);
  }}

  .col {{
    padding: 22px 24px;
  }}

  .col.mainstream {{ background: var(--mainstream-soft); }}
  .col.globalsouth {{ background: var(--globalsouth-soft); }}

  .fault-line {{
    background: repeating-linear-gradient(
      to bottom,
      var(--ink) 0px, var(--ink) 6px, transparent 6px, transparent 12px
    );
  }}

  .col-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
    display: block;
  }}
  .col.mainstream .col-label {{ color: var(--mainstream); }}
  .col.globalsouth .col-label {{ color: var(--globalsouth); }}

  .col p {{
    font-size: 14.5px;
    margin: 0 0 12px;
  }}

  .sources {{
    margin-top: 14px;
    padding-top: 10px;
    border-top: 1px solid rgba(0,0,0,0.12);
  }}
  .sources-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--ink-soft);
    display: block;
    margin-bottom: 6px;
  }}
  .sources ul {{
    margin: 0;
    padding-left: 18px;
    font-size: 12.5px;
  }}
  .sources li {{ margin-bottom: 4px; }}
  .sources a {{ color: inherit; text-decoration: none; border-bottom: 1px dotted var(--ink-soft); }}
  .sources a:hover {{ border-bottom-style: solid; }}

  .gauge-row {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 14px 8px;
    font-family: 'IBM Plex Mono', monospace;
  }}

  .gauge-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--ink-soft);
    writing-mode: vertical-rl;
    text-orientation: mixed;
  }}

  .gauge-segments {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}

  .gauge-seg {{
    width: 18px;
    height: 6px;
    background: var(--gauge-empty);
  }}
  .gauge-seg.filled {{
    background: linear-gradient(90deg, var(--globalsouth), var(--mainstream));
  }}

  .convergence-note {{
    text-align: center;
    font-size: 11px;
    color: var(--ink-soft);
    max-width: 110px;
    margin: 6px auto 0;
  }}

  footer {{
    margin-top: 64px;
    padding-top: 18px;
    border-top: 1px solid var(--rule);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11.5px;
    color: var(--ink-soft);
  }}

  @media (max-width: 720px) {{
    .split {{ grid-template-columns: 1fr; }}
    .fault-line {{ display: none; }}
    .masthead-title {{ font-size: 32px; }}
  }}
</style>
</head>
<body>
<div class="wrap">

  <header class="masthead">
    <div class="masthead-row">
      <h1 class="masthead-title">The Fault Line</h1>
      <div class="masthead-meta">ISSUE NO. {issue_no}<br>{issue_date}</div>
    </div>
    <p class="masthead-sub">A standing comparison of mainstream/Western-institutionalist and Global South / TWAIL readings of current international economic &amp; investment law developments.</p>
    <div class="legend">
      <span><span class="swatch" style="background:var(--mainstream)"></span>Mainstream / Institutionalist</span>
      <span><span class="swatch" style="background:var(--globalsouth)"></span>Global South / TWAIL</span>
    </div>
  </header>

  {topics_html}

  <footer>
    Generated automatically — verify all sources before citing. Convergence score: 1 = sharply opposed, 5 = largely converging.
  </footer>

</div>
</body>
</html>
"""

TOPIC_TEMPLATE = """
<section class="topic">
  <div class="topic-head">
    <span class="topic-no">{topic_no:02d}</span>
    <h2 class="topic-title">{title}</h2>
  </div>
  <p class="framing">{framing}</p>

  <div class="split">
    <div class="col mainstream">
      <span class="col-label">Mainstream / Institutionalist</span>
      <p>{mainstream_view}</p>
      {mainstream_sources_html}
    </div>

    <div class="fault-line"></div>

    <div class="col globalsouth">
      <span class="col-label">Global South / TWAIL</span>
      <p>{global_south_view}</p>
      {global_south_sources_html}
    </div>
  </div>

  <div class="gauge-row">
    <span class="gauge-label">CONVERGENCE</span>
    {gauge_segments}
    <span class="convergence-note">{convergence_note}</span>
  </div>
</section>
"""


def _esc(text: str) -> str:
    return html_lib.escape(text or "")


def _render_sources(label: str, sources: list[dict]) -> str:
    if not sources:
        return ""
    items = "".join(
        f'<li><a href="{_esc(s.get("url", "#"))}" target="_blank" rel="noopener">{_esc(s.get("title", "Untitled source"))}</a></li>'
        for s in sources
    )
    return f'<div class="sources"><span class="sources-label">{label}</span><ul>{items}</ul></div>'


def _render_gauge(score: int) -> str:
    score = max(1, min(5, int(score or 1)))
    segs = []
    for i in range(1, 6):
        cls = "gauge-seg filled" if i <= score else "gauge-seg"
        segs.append(f'<span class="{cls}"></span>')
    return f'<div class="gauge-segments">{"".join(segs)}</div>'


def render_html(analysis: dict, issue_no: int, issue_date: str) -> str:
    topics = analysis.get("topics", [])
    topic_blocks = []

    for idx, t in enumerate(topics, start=1):
        block = TOPIC_TEMPLATE.format(
            topic_no=idx,
            title=_esc(t.get("title", "Untitled topic")),
            framing=_esc(t.get("framing", "")),
            mainstream_view=_esc(t.get("mainstream_view", "")),
            global_south_view=_esc(t.get("global_south_view", "")),
            mainstream_sources_html=_render_sources("Sources", t.get("mainstream_sources", [])),
            global_south_sources_html=_render_sources("Sources", t.get("global_south_sources", [])),
            gauge_segments=_render_gauge(t.get("convergence_score", 1)),
            convergence_note=_esc(t.get("convergence_note", "")),
        )
        topic_blocks.append(block)

    if not topic_blocks:
        topic_blocks.append(
            '<p style="text-align:center;color:var(--ink-soft);margin-top:60px;">'
            "No topics were generated this run — check the pipeline logs.</p>"
        )

    return PAGE_TEMPLATE.format(
        issue_no=issue_no,
        issue_date=_esc(issue_date),
        topics_html="\n".join(topic_blocks),
    )
