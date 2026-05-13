# Local Business Competitor Analysis Agent

A production-grade AI system for comprehensive competitive intelligence analysis of local businesses. The agent analyzes competitors across multiple dimensions including products, pricing, SEO, social media, customer feedback, and strategic positioning.

## Features

- **Universal business support**: Works for many business types (restaurants, cafes, shops, services, and more).
- **7-step sequential analysis**: Discovery → product → pricing → SEO → social → news → customer feedback.
- **Data-driven reports**: Agents are instructed to use tools (search, scrape) and to mark unverified data clearly.
- **Multi-platform intelligence**: Web search, Firecrawl, Google Maps (optional Docker scraper), review-oriented research.
- **Advanced sections**: Personas, risk, recommendations, financial benchmarks, and more (optional; see [Advanced sections](#optional-advanced-sections)).
- **Google Maps scraper**: Docker-based integration for richer Maps-style data (optional).

## Quick start

### Prerequisites

- **Python 3.9+** (see `pyproject.toml`; 3.10+ recommended)
- **OpenRouter** API key ([openrouter.ai](https://openrouter.ai/keys))
- **Firecrawl** API key (agents use Firecrawl for structured page extraction)
- **Tavily** and **Serper** API keys (default tool stack registers both search providers)
- Optional: **Docker** (for Google Maps scraper)
- Optional: **YouTube Data API** key and `google-api-python-client` (channel stats after the social step)
- Optional: **Agent Reach** CLI ([install guide](https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md)) — detection on Windows uses `where agent-reach`

### Installation

1. Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd "COMPETITOR ANALYSIS AGENT"
```

2. Create a virtual environment (recommended), then install dependencies using **either** [uv](https://github.com/astral-sh/uv) **or** pip:

```bash
# Option A — uv (uses uv.lock when present)
uv sync

# Option B — pip editable install from pyproject.toml
pip install -e .
```

There is **no** `requirements.txt`; dependency versions are defined in `pyproject.toml` (and locked in `uv.lock` if you use uv).

3. Environment file — copy the template and fill in keys:

```bash
# Windows (PowerShell)
Copy-Item env.example .env

# macOS / Linux
cp env.example .env
```

Edit `.env` with your API keys. The committed template is `env.example` (not `.env.example`).

### Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENROUTER_API_KEY` | Yes | LLM calls via OpenRouter (Agno `OpenRouter` model) |
| `FIRECRAWL_API_KEY` | Yes for default tools | Website crawl / markdown extraction |
| `TAVILY_API_KEY` | Yes for default tools | Tavily search (`TavilyTools`) |
| `SERPER_API_KEY` | Yes for default tools | Google search (`SerperTools`) |
| `ENABLE_GOOGLE_MAPS_SCRAPER` | No | Set to `true` to enable Docker Google Maps scraper (requires Docker) |
| `YOUTUBE_API_KEY` | No | YouTube channel stats (also needs `google-api-python-client`) |
| `ENABLE_ADVANCED_SECTIONS` | No | Default `true` in code if unset; set `false` to skip the extra agent pass |
| `ENABLE_VISUAL_CHARTS` | No | ASCII positioning matrix and related visuals in the report |
| `STRICT_VERIFICATION` | No | Intended for strict data-handling behavior in agents (see `agent/config.py`) |

Example `.env` skeleton:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
FIRECRAWL_API_KEY=fc-...
TAVILY_API_KEY=tvly-...
SERPER_API_KEY=...

# Optional
ENABLE_GOOGLE_MAPS_SCRAPER=false
YOUTUBE_API_KEY=
ENABLE_ADVANCED_SECTIONS=true
ENABLE_VISUAL_CHARTS=true
STRICT_VERIFICATION=true
```

## Usage

### Basic analysis

```bash
python main_modular.py --company "Foodhallen" --domain "food hall" --location "Amsterdam"
```

### With initial competitors

```bash
python main_modular.py --company "Cafe de Klos" \
                       --domain "cafe" \
                       --location "Amsterdam" \
                       --initial_competitors "De Bolhoed, Cafe de Paris"
```

### Custom output path

```bash
python main_modular.py --company "Restaurant De Kas" \
                       --domain "restaurant" \
                       --location "Amsterdam" \
                       --output "./reports/analysis.md"
```

### Skip YouTube API calls

```bash
python main_modular.py --company "Foodhallen" --domain "restaurant" --location "Amsterdam" --skip-youtube
```

## Command-line options

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--company` | Yes | Target business name | `"Foodhallen"` |
| `--domain` | Yes | Business type or category | `"cafe"`, `"restaurant"`, `"gym"` |
| `--location` | Yes | Geographic focus | `"Amsterdam"` |
| `--initial_competitors` | No | Seed competitor names (comma-separated) | `"A, B"` (default label: `Auto-discovered`) |
| `--output` | No | Full path to the output Markdown file | `"./reports/out.md"` |
| `--skip-youtube` | No | Do not call YouTube Data API after the social step | flag |

## Supported business types

The prompts are written to adapt to the domain you pass in (`--domain`): food and beverage, retail, services, entertainment, professional services, and others. The pipeline does not hard-code “restaurant only” behavior in the orchestrator.

## Analysis pipeline

### Step 1: Competitor discovery

- Discovers **at least six** competitors when possible; uses search/scrape tools and optional Google Maps Docker scraper.
- Parses a markdown table and regex hints into **`shared_data`** (`competitor_list`, `competitor_count`).
- If discovery fails or returns too few competitors, runs a **search fallback** (Tavily, then Serper) and may pad with generic placeholders so later steps still run.

### Steps 2–7

2. **Product and service** — offerings and positioning versus the target.  
3. **Pricing and business model** — price signals, delivery platforms where relevant.  
4. **Local SEO and content** — visibility and content angles.  
5. **Social media** — presence and engagement.  
6. **News and market intelligence** — recent local signals.  
7. **Customer feedback** — reviews and sentiment-oriented synthesis.

Each step receives the discovered **competitor name list** so the model is steered to cover the same set.

### Bonus: SWOT and strategy

- Runs after step 7 when `shared_data` has a valid competitor count and list.
- Uses the **coordinator** model (see [Models](#models-and-openrouter)).

### Optional: advanced sections

When `ENABLE_ADVANCED_SECTIONS` is true, an additional agent generates extended blocks (personas, risk table, recommendations, financial framing, digital ads, UGC, accessibility, seasonal notes, action plan). The final report merges this output into dedicated sections when content is present and passes length checks.

**Note:** If advanced blocks appear empty or show “Insufficient data” placeholders, the pipeline may need alignment between how those headings are parsed and how the report inserts them; see `main_modular.py` and `agent/report_generator.py` when debugging.

## Output

### Report structure

Typical sections in order:

1. Executive summary  
2. Methodology  
3. Competitive landscape (discovery)  
4. Product and feature analysis  
5. Pricing and business models  
6. SEO and content strategy  
7. Social media intelligence (optional YouTube subsection)  
8. News and recent developments  
9. Customer feedback analysis  
10. Customer personas, SWOT, risk, recommendations, financial, ads, UGC, accessibility, seasonal, action plan — depending on `ENABLE_ADVANCED_SECTIONS` and available content  
11. Competitive positioning matrix (when visual charts are enabled)

### File format and naming

- **Format**: Markdown (UTF-8)  
- **Default directory**: `./output/` (created if missing)  
- **Default filename**: `competitor_analysis_{slug}_{YYYYMMDD_HHMM}.md`  
  where `slug` is derived from `company`, `domain`, and `location` (lowercased, spaces to underscores, max 50 characters).  
- **`--output`**: Writes exactly to the path you provide.

## Models and OpenRouter

Models are **not** read from environment variables in the current code. They are set in **`agent/config.py`**:

- **`COORDINATOR_MODEL`** — used for SWOT and advanced sections (higher-level synthesis).  
- **`AGENT_MODEL`** — used for the seven research agents.

Defaults in the repository point at OpenRouter model IDs (for example Grok for coordination and a GPT-OSS variant for workers). Change those constants to switch models, then rerun the CLI.

## Optional integrations

### Google Maps scraper (Docker)

1. Install and start Docker.  
2. Set `ENABLE_GOOGLE_MAPS_SCRAPER=true` in `.env`.  
3. The app runs `gosom/google-maps-scraper` with a **30-second** timeout and JSON-oriented output.

### Agent Reach

Install the Agent Reach CLI for optional deeper platform workflows. Availability is probed at import time on supported setups.

### Crawl4AI

Optional dependency (`crawl4ai`) for async browser-based scraping helpers in `agent/tools.py`. Agents primarily use Firecrawl + search tools unless you extend tooling.

## Performance and limits

- **Runtime**: Often on the order of **several minutes**, depending on model latency, tool calls, and network.  
- **Competitors**: Pipeline targets **six to ten** named competitors; fallback logic enforces a minimum list size for downstream steps.  
- **Report assembly**: Individual step outputs may be **truncated for the final Markdown merge** (see `clean_cutoff` in `agent/report_generator.py`) so very long agent replies are shortened before section stitching. Total file size still varies with templates, SWOT, advanced text, and charts.

## Troubleshooting

### API and keys

- Confirm `OPENROUTER_API_KEY` starts with `sk-or-v1-` (or the format OpenRouter documents).  
- Ensure Tavily, Serper, and Firecrawl keys match the providers your `agno` tool wrappers expect.

### Docker

- Google Maps scraping requires a working `docker` CLI and image pull on first use.

### Windows console encoding

- On some Windows terminals, importing the package can print Unicode status symbols from `agent/config.py`. If you see encoding errors, run with UTF-8 mode, for example:  
  `set PYTHONIOENCODING=utf-8` (cmd) or `$env:PYTHONIOENCODING='utf-8'` (PowerShell) before `python main_modular.py ...`.

### Debug logging

```bash
# PowerShell
$env:PYTHONPATH = "."
python main_modular.py --company "Test" --domain "restaurant" --location "Amsterdam" 2>&1 | Tee-Object -FilePath debug.log
```

```bash
# bash
export PYTHONPATH=.
python main_modular.py --company "Test" --domain "restaurant" --location "Amsterdam" 2>&1 | tee debug.log
```

## Examples

### Restaurant

```bash
python main_modular.py --company "Restaurant De Kas" \
                       --domain "restaurant" \
                       --location "Amsterdam"
```

### Cafe with seeds

```bash
python main_modular.py --company "Cafe de Klos" \
                       --domain "cafe" \
                       --location "Amsterdam" \
                       --initial_competitors "De Bolhoed, Cafe de Paris"
```

### Gym / service business

```bash
python main_modular.py --company "Fitness First" \
                       --domain "gym" \
                       --location "Amsterdam"
```

## Architecture

### Components

- **Entrypoint**: `main_modular.py` — CLI, sequential steps, `shared_data`, fallbacks, report save.  
- **Agents**: `agent/agents/*.py` — Agno `Agent` factories (discovery, product, pricing, SEO, social, news, feedback, SWOT, advanced).  
- **Tools**: `agent/tools.py` — Tavily, Serper, Firecrawl, optional Crawl4AI, YouTube, Docker Maps helper.  
- **Models**: `agent/models.py` — OpenRouter-backed models for coordinator vs worker roles.  
- **Report**: `agent/report_generator.py` — Markdown synthesis, tables, optional matrix.

### Data flow

```
CLI (company, domain, location)
    → Discovery → shared_data (competitor_count, competitor_list)
    → Product → Pricing → SEO → Social → News → Feedback
    → shared_data (price_position, google_reviews, …)
    → SWOT (coordinator)
    → Advanced sections (optional)
    → synthesize_final_report → output/*.md
```

## Contributing

1. Fork the repository  
2. Create a feature branch  
3. Make focused changes  
4. Add or update tests when behavior changes  
5. Open a pull request  

## License

This project is licensed under the MIT License — see the `LICENSE` file if present in your fork.

## Support

- **Technical depth**: `specs.md` (may differ slightly from the live code; prefer this README and source for behavior).  
- **Issues**: Use your host’s issue tracker (for example GitHub Issues).

## Changelog

### README refresh (May 2026)

- Documented `pyproject.toml` / `uv` installation (removed obsolete `requirements.txt` reference).  
- Documented `env.example`, required API keys, and `--skip-youtube`.  
- Aligned model documentation with `agent/config.py` (constants, not env vars).  
- Clarified output filename pattern, truncation behavior, and Windows notes.

### Version 1.0.0 (April 13, 2026)

- Initial public-style release: seven-step pipeline, optional Maps scraper and advanced sections, SWOT synthesis, shared competitor state.

---

**Competitor Analysis Agent**  
*README last updated: May 13, 2026*
