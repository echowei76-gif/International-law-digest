# The Fault Line — IEL/IIL Comparative Digest

Automated weekly digest comparing mainstream/Western-institutionalist and
Global South/TWAIL readings of current developments in international
economic law (IEL) and international investment law (IIL).

Pipeline: RSS feeds → Claude (with live web search) builds the comparison →
static HTML page → committed to `docs/` → served by GitHub Pages.

## Setup

### Option A — Anthropic (default, includes live web search)

1. **Create the repo** and push this folder's contents to it.

2. **Add your API key as a secret.**
   Repo → Settings → Secrets and variables → Actions → New repository secret
   - Name: `ANTHROPIC_API_KEY`
   - Value: your key from the Claude Platform console

3. Skip to step 3 ("Enable GitHub Pages") below — no further config needed,
   `LLM_PROVIDER` defaults to `anthropic`.

### Option B — DeepSeek

DeepSeek's API doesn't include a hosted web-search tool the way Anthropic's
does, so this path adds a manual search step via [Tavily](https://tavily.com)
(free tier: 1,000 searches/month). Without a Tavily key it still works, just
relying on the RSS digest plus DeepSeek's own training knowledge instead of
live search — fine for stable doctrinal topics, weaker for breaking news.

1. **Get a DeepSeek API key:** https://platform.deepseek.com → API Keys.

2. **(Recommended) Get a free Tavily key:** https://tavily.com → sign up →
   API Keys.

3. **Add secrets.** Repo → Settings → Secrets and variables → Actions:
   - `DEEPSEEK_API_KEY` → your DeepSeek key
   - `TAVILY_API_KEY` → your Tavily key (optional but recommended)

4. **Set the provider.** Repo → Settings → Secrets and variables → Actions →
   **Variables** tab → New repository variable:
   - Name: `LLM_PROVIDER`
   - Value: `deepseek`

   (This is a *variable*, not a *secret* — it's not sensitive, just a switch.)

5. To run it locally instead of through Actions:
   ```bash
   export LLM_PROVIDER=deepseek
   export DEEPSEEK_API_KEY="sk-..."
   export TAVILY_API_KEY="tvly-..."   # optional
   python src/main.py
   ```

### Then, for either provider:

3. **Enable GitHub Pages.**
   Repo → Settings → Pages → Source: "Deploy from a branch" → Branch: `main`,
   folder: `/docs`. After the first run, your digest will be live at
   `https://<your-username>.github.io/<repo-name>/`.

4. **Verify the feeds** before you trust the output blindly:
   ```
   pip install -r requirements.txt
   python src/validate_feeds.py
   ```
   This sandbox couldn't reach the actual feed domains while building this,
   so the URLs in `config/feeds.yaml` are best-effort guesses (mostly
   `/feed/` on WordPress sites). Run the validator from your own machine and
   fix any that report `[FAIL]` or `[WARN]`.

5. **Run it once manually** to check the output before waiting for Monday:
   Repo → Actions → "IEL/IIL Comparative Digest" → Run workflow.

## How it works

- `config/feeds.yaml` — your source list, each tagged `mainstream`,
  `global_south`, or `mixed`. Add/remove feeds freely; the tag is just
  context for the model, not a hard classification rule.
- `src/fetch_feeds.py` — pulls items published within `lookback_days`
  (default 7) from each feed.
- `src/analyze.py` — sends the RSS digest to Claude with the hosted
  `web_search` tool enabled. Claude picks the most significant current
  topics, verifies/supplements via search, and returns strict JSON: for
  each topic, a neutral framing, the mainstream view, the Global South/TWAIL
  view, a 1–5 convergence score, and real sources for each side.
- `src/build_html.py` — renders that JSON into the side-by-side HTML page
  (`docs/index.html`), with a "convergence gauge" per topic and a
  dotted/dashed "fault line" divider between the two columns.
- `src/main.py` — orchestrates the above, increments an issue counter in
  `data/state.json`, and archives every run to `docs/archive/`.
- `.github/workflows/digest.yml` — runs the whole thing every Monday
  08:00 UTC and commits the result. Change the cron expression for a
  different cadence.

## Tuning knobs (environment variables)

| Variable | Default | What it does |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` | `anthropic` or `deepseek`. Set as an Actions **variable**, not a secret. |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | (Anthropic only) Model used for analysis. Swap to `claude-opus-4-7` for deeper analysis at higher cost. |
| `DEEPSEEK_MODEL` | `deepseek-chat` | (DeepSeek only) Model used for analysis. |
| `MAX_TOPICS` | `6` | Number of topics generated per issue. |
| `LOOKBACK_DAYS` | `7` (or value in feeds.yaml) | How far back to pull RSS items. |

Set these in the workflow file's `env:` block, or as repo-level Actions
variables if you don't want to edit YAML each time.

## Known limitations / things to keep an eye on

- **RSS feed URLs drift.** Blogs migrate platforms. Re-run
  `validate_feeds.py` every few months.
- **The model can be wrong about "current."** Web search helps, but always
  spot-check a topic's framing before citing it in your own writing —
  treat this as a research lead generator, not a citable source.
- **DeepSeek path has a thinner research loop than Anthropic's.** It's two
  extra round-trips (propose queries → search → synthesize) instead of one
  call with a hosted tool, and the search quality depends entirely on
  Tavily results. If `TAVILY_API_KEY` isn't set, it's not searching the
  live web at all — just reasoning over the RSS digest and its own training
  data, which may be stale on fast-moving topics.
- **Cost.** Each run is one Claude API call with web search enabled
  (typically several search calls per run). Check your usage on the
  Claude Platform console if you increase `MAX_TOPICS` or run more often
  than weekly.
- **One-shot JSON.** If the model occasionally returns malformed JSON, the
  run will fail loudly in the Actions log rather than silently producing a
  broken page — check the Actions tab if `docs/index.html` doesn't update.
