# Local Business Competitor Analysis Agent

A production-grade AI system for comprehensive competitive intelligence analysis of local businesses. Built with multi-agent orchestration, it analyzes competitors across 7+ dimensions including products, pricing, SEO, social media, news, customer feedback, and strategic positioning.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Usage](#usage)
- [Configuration](#configuration)
- [Optional Integrations](#optional-integrations)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)
- [License](#license)

---

## Features

- **Universal Business Support**: Analyzes any business type (restaurants, cafes, gyms, shops, services, healthcare, etc.) via the `--domain` parameter
- **7-Step Sequential Pipeline**: Discovery → Product → Pricing → SEO → Social → News → Feedback
- **Multi-Agent Architecture**: Specialized agents for each analysis dimension using Agno
- **Data Verification**: Strict verification rules to mark unverified data; Google Maps scraper for authoritative review counts
- **Multi-Platform Intelligence**: Web search, Firecrawl scraping, optional Docker Google Maps scraper, review aggregation
- **Advanced Sections** (optional): Customer personas, risk assessment, actionable recommendations, financial benchmarks, digital ads, UGC analysis, accessibility review, seasonal trends, action plan
- **Visual Charts**: ASCII positioning matrix and sentiment charts in reports
- **Windows Ready**: UTF-8 encoding support, PowerShell compatible

---

## Quick Start

### Prerequisites

- **Python 3.9+** (3.10+ recommended)
- **OpenRouter** API key ([openrouter.ai](https://openrouter.ai/keys))
- **Firecrawl** API key ([firecrawl.dev](https://www.firecrawl.dev/api))
- **Tavily** API key ([tavily.com](https://tavily.com))
- **Serper** API key ([serper.dev](https://serper.dev))

### Installation with uv (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd "COMPETITOR ANALYSIS AGENT"

# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows PowerShell

# Install dependencies
uv sync

# Or install in editable mode
uv pip install -e .
```

### Environment Setup

1. Create a `.env` file from the example:

```bash
# Windows
Copy-Item env.example .env

# Linux/Mac
cp env.example .env
```

2. Edit `.env` with your API keys:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-key
FIRECRAWL_API_KEY=fc-your-key
TAVILY_API_KEY=tvly-your-key
SERPER_API_KEY=your-serper-key
```

### Run Analysis

```bash
# Basic usage
python main_modular.py --company "Foodhallen" --domain "food hall" --location "Amsterdam"

# With initial competitors
python main_modular.py --company "Cafe de Klos" --domain "cafe" --location "Amsterdam" --initial_competitors "De Bolhoed, The Bulldog"
```

---

## Project Structure

```
COMPETITOR-ANALYSIS-AGENT/
├── main_modular.py              # CLI entry point, pipeline orchestration
├── pyproject.toml               # Project metadata, dependencies (uv)
├── env.example                  # Environment variable template
├── README.md                    # This file
├── specs.md                     # Detailed technical specifications
│
├── agent/                       # Core package
│   ├── __init__.py              # Package metadata
│   ├── config.py                # Configuration, model settings, optional integrations
│   ├── models.py                # Data models (CompetitorProfile, etc.)
│   ├── tools.py                 # Search/scraping tools, YouTube API, Docker helper
│   ├── report_generator.py      # Markdown report synthesis, tables, charts
│   │
│   └── agents/                  # Specialized analysis agents
│       ├── __init__.py          # Agent exports
│       ├── competitor_discovery_agent.py   # Find and profile competitors
│       ├── product_analysis_agent.py      # Product/service offerings analysis
│       ├── pricing_business_agent.py      # Pricing and business model analysis
│       ├── seo_content_agent.py           # Local SEO analysis
│       ├── social_media_agent.py          # Social media presence analysis
│       ├── news_intelligence_agent.py     # Local news and market intelligence
│       ├── customer_feedback_agent.py     # Customer reviews and sentiment
│       ├── swot_synthesis_agent.py        # Strategic SWOT analysis
│       └── advanced_sections_agent.py     # Extended strategic sections
│
└── output/                      # Generated reports (auto-created)
    └── competitor_analysis_*.md # Analysis reports
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     main_modular.py (CLI + Orchestration)           │
│                                                                      │
│  ┌──────────────┐  shared_data  ┌──────────────────────────────┐   │
│  │   Arguments  │ ─────────────▶│  7-Step Sequential Pipeline  │   │
│  │  (company,   │               │                               │   │
│  │   domain,    │               │  1. Competitor Discovery      │   │
│  │   location)  │               │      ↓                        │   │
│  └──────────────┘               │  2. Product Analysis          │   │
│                                │      ↓                        │   │
│                                │  3. Pricing Analysis          │   │
│                                │      ↓                        │   │
│                                │  4. SEO Analysis              │   │
│                                │      ↓                        │   │
│                                │  5. Social Media              │   │
│                                │      ↓                        │   │
│                                │  6. News Intelligence         │   │
│                                │      ↓                        │   │
│                                │  7. Customer Feedback        │   │
│                                └──────────────────────────────┘   │
│                                            │                       │
│                                     SWOT Synthesis                  │
│                                            │                       │
│                                    Advanced Sections (optional)      │
│                                            │                       │
│                                      Report Generation              │
│                                            │                       │
│                                     output/*.md Report              │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Architecture

Each agent is an **Agno Agent** factory that:
- Uses a specific model (coordinator vs agent tier)
- Has access to search/scraping tools
- Receives detailed instructions for domain-specific analysis
- Returns structured markdown output

**Model Tiering:**
| Agent | Model | Purpose |
|-------|-------|---------|
| Discovery, Product, Pricing, SEO, Social, News, Feedback | `AGENT_MODEL` | Efficient data extraction |
| SWOT, Advanced Sections | `COORDINATOR_MODEL` | High-quality synthesis |

### Data Flow

1. **CLI Input**: `company`, `domain`, `location`, `initial_competitors`
2. **Discovery**: Extracts competitor list and count → `shared_data`
3. **Analysis Steps 2-7**: Each agent receives competitor list, outputs markdown
4. **Price Extraction**: Parses `{company}` section for price position → `shared_data`
5. **Feedback Extraction**: Parses Google review counts → `shared_data['google_reviews']`
6. **SWOT Synthesis**: Uses `shared_data` for data-driven analysis
7. **Report Generation**: Merges all outputs with validation, charts, positioning matrix

---

## Usage

### Command-Line Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--company` | Yes | - | Target business name |
| `--domain` | Yes | - | Business type (e.g., "cafe", "restaurant", "gym") |
| `--location` | Yes | - | Geographic location |
| `--initial_competitors` | No | "Auto-discovered" | Comma-separated seed competitors |
| `--output` | No | `./output/` | Custom output file path |
| `--skip-youtube` | No | False | Skip YouTube API calls |

### Usage Examples

#### Basic Restaurant Analysis
```bash
python main_modular.py --company "Foodhallen" --domain "food hall" --location "Amsterdam"
```

#### Cafe with Seed Competitors
```bash
python main_modular.py --company "Cafe de Klos" \
                       --domain "cafe" \
                       --location "Amsterdam" \
                       --initial_competitors "De Bolhoed, The Bulldog, Coffee Ju爷"
```

#### Service Business (Gym)
```bash
python main_modular.py --company "Fitness First" --domain "gym" --location "Amsterdam"
```

#### Custom Output Path
```bash
python main_modular.py --company "Restaurant De Kas" \
                       --domain "restaurant" \
                       --location "Amsterdam" \
                       --output "./reports/de-kas-analysis.md"
```

#### Skip YouTube API
```bash
python main_modular.py --company "Foodhallen" --domain "restaurant" \
                       --location "Amsterdam" --skip-youtube
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key for LLM calls |
| `FIRECRAWL_API_KEY` | Yes | - | Firecrawl API key for web scraping |
| `TAVILY_API_KEY` | Yes | - | Tavily search API key |
| `SERPER_API_KEY` | Yes | - | Serper (Google) search API key |
| `ENABLE_GOOGLE_MAPS_SCRAPER` | No | `false` | Enable Docker Google Maps scraper |
| `YOUTUBE_API_KEY` | No | - | YouTube Data API key |
| `ENABLE_ADVANCED_SECTIONS` | No | `true` | Generate advanced strategic sections |
| `ENABLE_VISUAL_CHARTS` | No | `true` | Enable ASCII charts in reports |
| `STRICT_VERIFICATION` | No | `true` | Strict data verification mode |

### Model Configuration

Models are configured in `agent/config.py`:

```python
COORDINATOR_MODEL = "x-ai/grok-4.3"        # High reasoning for synthesis
AGENT_MODEL = "openai/gpt-oss-120b:nitro"  # Fast extraction for agents
```

To change models, edit these constants and restart.

---

## Optional Integrations

### Google Maps Scraper (Docker)

Rich Maps-style data including review counts, ratings, coordinates:

```bash
# 1. Install Docker
# 2. Enable in .env
echo "ENABLE_GOOGLE_MAPS_SCRAPER=true" >> .env

# 3. Run analysis
python main_modular.py --company "Foodhallen" --domain "food hall" --location "Amsterdam"
```

### Agent Reach CLI

Enhanced platform access for Twitter, Reddit, GitHub:

```bash
# Install: https://github.com/Panniantong/agent-reach
# Follow installation guide

python main_modular.py --company "Foodhallen" --domain "food hall" --location "Amsterdam"
```

### Crawl4AI

Open-source async browser scraping (optional supplement):

```bash
pip install crawl4ai && crawl4ai-setup
```

### YouTube Data API

Channel statistics in reports:

```bash
# Add to .env
YOUTUBE_API_KEY=your-youtube-api-key

# Skip if not configured
python main_modular.py --company "Foodhallen" --domain "restaurant" --location "Amsterdam" --skip-youtube
```

---

## Performance

| Metric | Typical Value |
|--------|---------------|
| **Execution Time** | 3-5 minutes |
| **Report Size** | 30,000-60,000 characters |
| **Competitors Analyzed** | 6-10 per run |
| **Review Platforms** | 8+ sources per competitor |
| **Sections in Report** | 10-19 (with advanced) |

### Optimization Tips

1. **Use `--skip-youtube`** if YouTube isn't relevant
2. **Disable advanced sections** with `ENABLE_ADVANCED_SECTIONS=false` for faster runs
3. **Provide initial competitors** to reduce discovery time
4. **Ensure stable API connectivity** to OpenRouter

---

## Troubleshooting

### API Key Issues

```bash
# Verify key format
# OpenRouter should start with: sk-or-v1-
# Tavily: tvly-
# Firecrawl: fc-
```

### Windows UTF-8 Encoding

```powershell
# Set before running
$env:PYTHONIOENCODING = "utf-8"
python main_modular.py --company "Foodhallen" --domain "food hall" --location "Amsterdam"
```

### Docker (Google Maps Scraper)

```bash
# Verify Docker is installed and running
docker --version

# Manual image pull (optional)
docker pull gosom/google-maps-scraper
```

### Debug Logging

```powershell
$env:PYTHONPATH = "."
python main_modular.py --company "Test" --domain "restaurant" --location "Amsterdam" 2>&1 | Tee-Object -FilePath debug.log
```

### Empty Report Sections

If sections show "Insufficient data":
1. Check API keys are valid
2. Verify internet connectivity
3. Try with `--initial_competitors` to seed the analysis
4. Check logs for specific agent errors

---

## Examples

### Restaurant in Amsterdam

```bash
python main_modular.py --company "Foodhallen" \
                       --domain "food hall" \
                       --location "Amsterdam"
```

### Cafe with Seeds

```bash
python main_modular.py --company "Cafe de Klos" \
                       --domain "cafe" \
                       --location "Amsterdam" \
                       --initial_competitors "De Bolhoed, Cafe de Paris"
```

### Gym Analysis

```bash
python main_modular.py --company "Basic Fit" \
                       --domain "gym" \
                       --location "Berlin" \
                       --initial_competitors "McFit, FitX"
```

### Berlin Coffee Shop (with output)

```bash
python main_modular.py --company "The Barn" \
                       --domain "coffee shop" \
                       --location "Berlin" \
                       --output "./reports/barn_berlin.md"
```

---

## Development

### Adding a New Agent

1. Create `agent/agents/your_agent.py`:

```python
from agno.agent import Agent
from ..models import agent_model
from ..tools import all_tools

def your_agent() -> Agent:
    return Agent(
        name="Your Agent Name",
        role="Describe agent purpose",
        model=agent_model(),
        tools=all_tools(),
        instructions=[
            "Detailed instructions...",
        ],
        markdown=True,
    )
```

2. Export in `agent/agents/__init__.py`
3. Import in `main_modular.py`
4. Add to pipeline in `main()` function

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Format
uv run black .

# Lint
uv run flake8 .

# Type check
uv run mypy agent/
```

---

## License

MIT License - see LICENSE file in repository.

---

## Support

- **Technical Documentation**: See `specs.md` for detailed specifications
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: GitHub Discussions for questions

---
