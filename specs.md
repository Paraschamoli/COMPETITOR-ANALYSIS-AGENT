# Local Business Competitor Analysis Agent - Technical Specification

## Executive Overview

The Local Business Competitor Analysis Agent is a production-grade AI system for analyzing any type of local business across all categories. It combines multi-agent orchestration with sequential workflow execution to deliver comprehensive competitive intelligence reports.

**Architecture:** Sequential Pipeline with Shared Data State  
**Performance:** 30,000-60,000 character reports in 3-5 minutes  
**Business Support:** ANY business type via `--domain` parameter

---

## System Architecture

### Core Components

```
CLI Input (main_modular.py)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│              7-Step Sequential Pipeline                  │
│                                                          │
│  1. Competitor Discovery → shared_data['competitor_*']  │
│  2. Product Analysis                                     │
│  3. Pricing Analysis → shared_data['price_position']    │
│  4. SEO Analysis                                         │
│  5. Social Media Intelligence                            │
│  6. News Intelligence                                     │
│  7. Customer Feedback → shared_data['google_reviews']   │
│                                                          │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│           Bonus Steps (Data-Driven Synthesis)           │
│                                                          │
│  - SWOT Synthesis (uses coordinator_model)              │
│  - Advanced Sections (optional, uses coordinator_model) │
│                                                          │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                   Report Generation                      │
│                                                          │
│  - Markdown synthesis with validation                   │
│  - Visual charts (positioning matrix, sentiment)        │
│  - UTF-8 output to ./output/                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## File Structure

```
agent/
├── __init__.py                 # Package metadata (v1.0.0)
├── config.py                   # Model config, optional integrations
├── models.py                   # Pydantic models (CompetitorProfile)
├── tools.py                    # Search/scraping tools, YouTube, Docker
├── report_generator.py         # Markdown synthesis, charts, validation
│
└── agents/
    ├── __init__.py             # Agent exports
    ├── competitor_discovery_agent.py
    ├── product_analysis_agent.py
    ├── pricing_business_agent.py
    ├── seo_content_agent.py
    ├── social_media_agent.py
    ├── news_intelligence_agent.py
    ├── customer_feedback_agent.py
    ├── swot_synthesis_agent.py
    └── advanced_sections_agent.py

main_modular.py                 # CLI + orchestration + shared_data
pyproject.toml                  # Dependencies (uv)
specs.md                        # This file
```

---

## Agent Specifications

### Model Configuration

| Constant | Default Value | Purpose | File |
|----------|--------------|---------|------|
| `COORDINATOR_MODEL` | `x-ai/grok-4.3` | High-quality synthesis | `config.py` |
| `AGENT_MODEL` | `openai/gpt-oss-120b:nitro` | Efficient extraction | `config.py` |

### 1. Competitor Discovery Agent

**File:** `agent/agents/competitor_discovery_agent.py`  
**Model:** `agent_model()` (AGENT_MODEL)  
**Tools:** `all_tools()` + `google_maps_scraper_tool()` (if Docker)

**Responsibilities:**
- Discover 6-10 competitors via Google Maps scraper or search fallback
- Verify addresses, ratings, review counts
- Output comparison matrix with verification column

**Output:** Markdown table with Name, Address, Rating, Review Count, Price Range, Verification

### 2. Product Analysis Agent

**File:** `agent/agents/product_analysis_agent.py`  
**Model:** `agent_model()`  
**Tools:** `all_tools()`

**Responsibilities:**
- Analyze offerings for every discovered competitor
- Verify accessibility claims (mark unverified as "Needs confirmation")
- Output per-competitor sections with location, offerings, business model, facilities

### 3. Pricing & Business Model Agent

**File:** `agent/agents/pricing_business_agent.py`  
**Model:** `agent_model()`  
**Tools:** `all_tools()`

**Responsibilities:**
- Extract pricing for every competitor
- Analyze delivery platform presence (UberEats, Deliveroo, etc.)
- Output pricing tables with verification column

### 4. SEO Content Agent

**File:** `agent/agents/seo_content_agent.py`  
**Model:** `agent_model()`  
**Tools:** `all_tools()`

**Responsibilities:**
- Audit target company first, then competitors
- Analyze Google Maps ranking, local citations, review platforms
- Output metrics table with strengths/weaknesses per competitor

### 5. Social Media Agent

**File:** `agent/agents/social_media_agent.py`  
**Model:** `agent_model()`  
**Tools:** `search_tools()` (no crawl)

**Responsibilities:**
- Analyze Instagram, Facebook, Google Business, YouTube presence
- Use Agent Reach if available for enhanced platform access
- Output platform table with follower counts and engagement

### 6. News Intelligence Agent

**File:** `agent/agents/news_intelligence_agent.py`  
**Model:** `agent_model()`  
**Tools:** `all_tools()`

**Responsibilities:**
- Track 6 months of local news per competitor
- Check for expansions, awards, partnerships, events
- Output location changes, events, awards, community partnerships

### 7. Customer Feedback Agent

**File:** `agent/agents/customer_feedback_agent.py`  
**Model:** `agent_model()`  
**Tools:** `all_tools()` + `google_maps_scraper_tool()` (if Docker)

**Responsibilities:**
- Mine reviews from Google, Yelp, TripAdvisor, Facebook
- Use Google Maps scraper as single source of truth for review counts
- Output sentiment analysis, theme clustering, verified quotes

### 8. SWOT Synthesis Agent

**File:** `agent/agents/swot_synthesis_agent.py`  
**Model:** `coordinator_model()` (COORDINATOR_MODEL)  
**Tools:** None (synthesis only)

**Responsibilities:**
- Per-competitor SWOT tables
- Strategic recommendations for target company
- Uses `competitor_count` from `shared_data` (not hardcoded)

### 9. Advanced Sections Agent

**File:** `agent/agents/advanced_sections_agent.py`  
**Model:** `coordinator_model()`  
**Tools:** None (synthesis only)

**Responsibilities:** Generates 9 sections:
1. Customer Personas (verified quotes only)
2. Risk Assessment (5 threats with mitigation)
3. Actionable Recommendations (prioritized table)
4. Financial Benchmarks (with source citations)
5. Digital Ads & Paid Media
6. UGC & Hashtag Analysis
7. Accessibility & Inclusivity (verification required)
8. Seasonal Trends (with source citations)
9. Next Steps / Action Plan

---

## Data Models

### CompetitorProfile (Pydantic)

```python
class CompetitorProfile(BaseModel):
    name: str
    address: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_tier: Optional[str] = None  # "Budget" | "Mid-range" | "Premium"
    website: Optional[str] = None
    hours: Optional[str] = None
```

### shared_data Dictionary

| Key | Type | Source | Used By |
|-----|------|--------|---------|
| `competitor_count` | int | Discovery table parsing | SWOT, Report |
| `competitor_list` | List[dict] | Discovery table parsing | All agents |
| `canonical_reviews` | dict | Discovery data | Downstream prompts |
| `google_reviews` | dict | Feedback extraction / scraper | Report (override) |
| `price_position` | str | Pricing section parsing | Report, SWOT |
| `per_competitor_prices` | dict | Pricing section parsing | Positioning matrix |

---

## Tool Configuration

### Search Tools

```python
def search_tools():
    return [TavilyTools(), SerperTools()]

def crawl_tools():
    return [FirecrawlTools()]
```

### Optional Tools

| Tool | Module | Availability Check |
|------|--------|-------------------|
| Crawl4AI | `crawl4ai` | `CRAWL4AI_AVAILABLE` |
| Agent Reach | subprocess | `AGENT_REACH_AVAILABLE` |
| YouTube API | `googleapiclient` | `YOUTUBE_AVAILABLE` |
| Google Maps Scraper | Docker | `GOOGLE_MAPS_SCRAPER_AVAILABLE` |

---

## Report Generation

### Output Sections (10-19 depending on configuration)

1. **Executive Summary** - Data-driven with competitor_count, price_position, top praise
2. **Methodology** - Research approach and data sources
3. **Competitive Landscape** - Discovery table + narrative
4. **Product & Feature Analysis** - Per-competitor offerings
5. **Pricing & Business Models** - Pricing tables, delivery analysis
6. **SEO & Content Strategy** - Local SEO metrics
7. **Social Media Intelligence** - Platform analysis + YouTube (optional)
8. **News & Recent Developments** - Local intelligence
9. **Customer Feedback Analysis** - Sentiment, themes, verified quotes
10. **Customer Personas** - (Advanced)
11. **SWOT Analysis & Recommendations** - Per-competitor SWOT
12. **Risk Assessment** - (Advanced)
13. **Actionable Recommendations** - (Advanced)
14. **Financial Benchmarks** - (Advanced)
15. **Digital Ads & Paid Media** - (Advanced)
16. **UGC & Hashtag Analysis** - (Advanced)
17. **Accessibility & Inclusivity** - (Advanced)
18. **Seasonal Trends** - (Advanced)
19. **Next Steps / Action Plan** - (Advanced)

### Visual Charts

- **Sentiment Bar Chart**: ASCII bars showing positive/neutral/negative percentages
- **Positioning Matrix**: 2x2 grid (Price vs Experience) with competitor names

---

## CLI Interface

### Arguments

| Argument | Required | Type | Default | Description |
|----------|----------|------|---------|-------------|
| `--company` | Yes | str | - | Target business name |
| `--domain` | Yes | str | - | Business type/category |
| `--location` | Yes | str | - | Geographic location |
| `--initial_competitors` | No | str | "Auto-discovered" | Seed competitors |
| `--output` | No | str | None | Custom output path |
| `--skip-youtube` | No | flag | False | Skip YouTube API |

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | LLM API key |
| `FIRECRAWL_API_KEY` | Yes | - | Web scraping |
| `TAVILY_API_KEY` | Yes | - | Search |
| `SERPER_API_KEY` | Yes | - | Search |
| `ENABLE_GOOGLE_MAPS_SCRAPER` | No | `false` | Docker scraper |
| `YOUTUBE_API_KEY` | No | - | Channel stats |
| `ENABLE_ADVANCED_SECTIONS` | No | `true` | Extra sections |
| `ENABLE_VISUAL_CHARTS` | No | `true` | ASCII charts |
| `STRICT_VERIFICATION` | No | `true` | Data verification |

---

## Error Handling

### Per-Step Error Handling

Each pipeline step is wrapped in `run_step()` with:
- 3 retries with exponential backoff (5s, 10s, 15s)
- Graceful fallback to empty placeholder on failure
- Logging of errors and retries

### Discovery Fallback

If discovery fails or returns <6 competitors:
1. Use Tavily for search fallback
2. Use Serper as secondary fallback
3. Validate business names with follow-up searches
4. Reject aggregator/editorial titles
5. Accept available competitors if minimum cannot be met

### Truncation Prevention

- `clean_cutoff()` truncates at sentence/word boundaries
- Logs warnings when truncation occurs
- Applied to all agent outputs before report synthesis

---

## Verification Rules

### Data Verification

1. **Single Source of Truth**: Google Maps (scraper or search) for review counts
2. **Cross-Check**: Verify key data points from 2+ sources
3. **Conflict Resolution**: Use most recent/reliable source, note discrepancies
4. **Numerical Consistency**: Same rating/review count across all sections

### Quote Verification

- Only use quotes from: Google Reviews, Yelp, TripAdvisor, Facebook Reviews
- Include platform name and date (YYYY-MM-DD) for each quote
- Reject quotes from: blogs, magazines, news articles
- Never use "derived from review analysis" language

### Accessibility Verification

- NEVER assume wheelchair access, parking, or accessibility features
- Mark unverified as "Needs confirmation"
- Verify from official sources (website, Google Business Profile)

---

## Performance Metrics

| Metric | Typical | Notes |
|--------|---------|-------|
| Execution Time | 3-5 min | Varies with API latency |
| Report Size | 30-60K chars | Depends on data availability |
| Competitors | 6-10 | Discovery target |
| Review Sources | 8+ | Per competitor |
| Report Sections | 10-19 | With/without advanced |

---

## Installation (uv)

```bash
# Clone and enter
git clone <repo>
cd "COMPETITOR ANALYSIS AGENT"

# Setup with uv
uv venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv sync

# Setup environment
Copy-Item env.example .env
# Edit .env with API keys

# Run
python main_modular.py --company "Foodhallen" --domain "food hall" --location "Amsterdam"
```

---

## Dependencies

### Core (Required)

- `agno` - Multi-agent orchestration
- `openai` - API compatibility
- `agno.tools.tavily` - Search
- `agno.tools.serper` - Search
- `agno.tools.firecrawl` - Scraping
- `pydantic` - Data models
- `python-dotenv` - Environment
- `duckduckgo-search` - Fallback search

### Optional

- `crawl4ai` - Async browser scraping
- `google-api-python-client` - YouTube API
- `playwright` - Browser automation
- `beautifulsoup4`, `lxml` - HTML parsing

### Visualization

- `matplotlib`, `seaborn`, `plotly` - Charts (in dependencies)
- Word cloud, networkx - Analysis tools

---

*Specification last updated: May 14, 2026*