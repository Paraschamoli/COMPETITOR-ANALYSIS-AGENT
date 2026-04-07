# COMPETITOR ANALYSIS AGENT

**AI-powered competitive intelligence system** that combines multi-agent teams with sequential workflow execution to deliver comprehensive competitor analysis reports.

## Features

- **Single Company Input**: Analyze any company and auto-discover 8-15 competitors
- **Hybrid Architecture**: Mix of individual agents and coordinated teams
- **Comprehensive Analysis**: 7-step pipeline covering all competitive dimensions
- **Multi-Source Data**: Search engines + web scraping for deep intelligence
- **Professional Reports**: 12-section structured reports with actionable insights

## Architecture

### Hybrid Team + Workflow System

```
User Input (CLI)
    |
    v
Mixed Execution Pipeline (7 Steps)
    |
    +-- Step 1: Competitor Discovery (Individual Agent)
    +-- Step 2: Product Analysis (Individual Agent)
    +-- Step 3: Research Team (5 Agents Parallel)
    |   |-- SEO Agent
    |   |-- Social Media Agent
    |   |-- News Agent
    |   |-- Product Agent
    |   |-- Pricing Agent
    +-- Step 4: Business Model Analysis (Individual Agent)
    +-- Step 5: Digital Marketing Analysis (Individual Agent)
    +-- Step 6: Customer Feedback Analysis (Individual Agent)
    +-- Step 7: SWOT Analysis (Individual Agent)
    |
    v
Final Synthesis Team
    |
    v
Comprehensive Report (30-80 pages)
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **AI Framework** | Agno | Agent orchestration & workflow |
| **Language Models** | OpenRouter (GPT-5.4) | Natural language processing |
| **Search Engines** | Tavily + Serper | Comprehensive web search |
| **Web Scraping** | Firecrawl | Direct content extraction |
| **CLI Interface** | Python argparse | Command-line interaction |

## Quick Start

### 1. Installation

```bash
# Clone and setup
git clone <repository>
cd competitor-analysis-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
OPENROUTER_API_KEY=your_openrouter_api_key
TAVILY_API_KEY=your_tavily_api_key
SERPER_API_KEY=your_serper_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

### 3. Get API Keys

| Service | URL | Cost |
|---------|-----|------|
| **OpenRouter** | https://openrouter.ai/keys | Pay-per-use |
| **Tavily** | https://tavily.com | Free tier available |
| **Serper** | https://serper.dev | Free tier available |
| **Firecrawl** | https://www.firecrawl.dev | Free tier available |

## Usage

### Basic Usage

```bash
# Analyze a single company (auto-discovers competitors)
python main.py --company "Stripe" --domain "payment processing"

# With initial competitors hint
python main.py --company "Notion" --domain "note-taking apps" --initial_competitors "Obsidian"

# Custom output location
python main.py --company "Vercel" --domain "developer hosting" --output "./reports/vercel_analysis.md"
```

### Command Structure

```bash
python main.py --company <COMPANY> --domain <DOMAIN> [--initial_competitors <COMPETITORS>] [--output <PATH>]
```

**Parameters:**
- `--company` (Required): Target company to analyze
- `--domain` (Required): Market domain/industry  
- `--initial_competitors` (Optional): Known competitors to start with
- `--output` (Optional): Custom output file path

### Usage Examples

```bash
# Payment processing analysis
python main.py --company "Stripe" --domain "payment processing"

# Note-taking apps analysis
python main.py --company "Notion" --domain "note-taking apps" --initial_competitors "Obsidian"

# Developer hosting analysis
python main.py --company "Vercel" --domain "developer hosting"

# CRM software analysis
python main.py --company "Salesforce" --domain "crm software" --output "./salesforce_competitors.md"

# E-commerce platforms
python main.py --company "Shopify" --domain "e-commerce platforms"
```

## Pipeline Execution

### 7-Step Analysis Process

| Step | Agent/Team | Purpose | Output |
|------|------------|---------|--------|
| **1** | Competitor Discovery | Auto-discover 8-15 competitors | Categorized competitor list |
| **2** | Product Analysis | Comprehensive feature comparison | Product comparison matrix |
| **3** | Research Team | Parallel multi-dimensional analysis | SEO, Social, News, Product, Pricing data |
| **4** | Business Model | Sales channels and GTM analysis | Business model comparison |
| **5** | Digital Marketing | Platform presence and strategy analysis | Marketing intelligence |
| **6** | Customer Feedback | Sentiment and review analysis | Customer insights |
| **7** | SWOT Analysis | Strategic positioning assessment | SWOT analysis |

### Report Structure

The generated report includes **12 comprehensive sections**:

1. **Executive Summary** - Key findings and strategic insights
2. **Target Company Analysis** - Detailed profile of the focus company
3. **Competitive Landscape** - Market overview and competitor categorization
4. **Product Comparison Matrix** - Feature-by-feature comparison
5. **Research Team Findings** - SEO, Social, News, Product, Pricing analysis
6. **Business Model Analysis** - Sales channels and GTM strategies
7. **Digital Marketing Analysis** - Platform presence and content strategies
8. **Customer Feedback Summary** - Sentiment analysis and user insights
9. **SWOT Analysis** - Strategic positioning for all competitors
10. **Strategic Recommendations** - Actionable insights and next steps
11. **Market Positioning Analysis** - Competitive positioning map
12. **Competitive Intelligence Summary** - Key takeaways and trends

## Sample Output

### Report Excerpt

```markdown
# Payment Processing Competitor Analysis Report
**Focus:** Stripe, Braintree, Adyen, PayPal  
**Domain:** Payment Processing

## Executive Summary

Stripe leads the payment processing market with superior developer experience,
comprehensive product ecosystem, and strong innovation velocity. The company
has successfully positioned itself as a financial infrastructure platform rather
than just a payment processor...

## Competitive Landscape

| Competitor | Category | Market Position | Key Strength |
|------------|----------|-----------------|--------------|
| Stripe | Market Leader | #1 | Developer experience |
| Braintree | Challenger | #3 | PayPal ecosystem |
| Adyen | Enterprise | #2 | Global reach |
| PayPal | Incumbent | #4 | Brand recognition |

## Product Comparison Matrix

| Feature | Stripe | Braintree | Adyen | PayPal |
|----------|--------|-----------|--------|---------|
| API Quality | Excellent | Good | Good | Fair |
| Global Reach | 135+ countries | 45+ countries | 200+ countries | 200+ countries |
| Developer Docs | Excellent | Good | Good | Basic |
| Pricing | 2.9% + $0.30 | 2.9% + $0.30 | Custom | 2.9% + $0.30 |
```

## Customization

### Model Configuration

Update model settings in `main.py`:

```python
# Model configuration
COORDINATOR_MODEL = "openai/gpt-5.4"  # For coordination and synthesis
AGENT_MODEL = "openai/gpt-5.4"       # For individual agents

# Alternative models available via OpenRouter:
# "openai/gpt-4o"           # Balanced performance
# "openai/gpt-4o-mini"      # Cost-effective
# "anthropic/claude-opus-4-5"  # Advanced reasoning
```

### Adding New Agents

Follow the existing agent pattern:

```python
def new_specialist_agent() -> Agent:
    return Agent(
        name="New Specialist",
        role="Agent role description",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "Detailed task instructions...",
        ],
        markdown=True,
    )
```

Then add to the appropriate team or pipeline step.

### Tool Configuration

Modify tool usage in the helper functions:

```python
def search_tools():
    """Configure search engines"""
    return [TavilyTools(), SerperTools()]  # Both for comprehensive coverage

def crawl_tools():
    """Configure web scraping"""
    return FirecrawlTools()
```

## Performance & Cost

### Execution Metrics

| Metric | Typical Range |
|--------|---------------|
| **Execution Time** | 5-15 minutes |
| **Report Length** | 30-80 pages |
| **Competitors Analyzed** | 8-15 companies |
| **Data Sources** | 20-50 websites |
| **API Calls** | 50-100 calls |

### Estimated Cost Per Run

| Component | Estimated Cost |
|-----------|----------------|
| **OpenRouter Models** | $0.10 - $0.30 |
| **Tavily Search** | $0.01 - $0.05 |
| **Serper Search** | $0.01 - $0.05 |
| **Firecrawl Scraping** | $0.02 - $0.10 |
| **Total** | **$0.14 - $0.50** |

*Costs vary based on model selection, competitor count, and data availability.*

## Error Handling

### Expected Limitations

Some websites block automated scraping:
- **LinkedIn**: Requires authentication
- **Twitter/X**: Anti-bot protection
- **Some protected sites**: Rate limiting

### Fallback Strategies

- **Search Fallback**: Use search results when scraping fails
- **Multiple Sources**: Cross-reference data from multiple sources
- **Graceful Degradation**: Continue analysis with available data
- **Limitation Notes**: Explicitly mention data limitations in reports

## File Structure

```
competitor-analysis-agent/
    |
    |-- main.py              # Main application entry point
    |-- requirements.txt     # Python dependencies
    |-- .env                 # API keys (create from .env.example)
    |-- README.md           # This file
    |-- specs.md            # Technical specifications
    |-- doc.md              # Detailed documentation
    |-- output/             # Generated reports (auto-created)
    |   |-- competitor_analysis_company_domain_timestamp.md
    |
    |-- main_old.py         # Original parallel team version
    |-- .env.example        # Environment template
```

## Documentation

- **`specs.md`** - Complete technical specifications
- **`doc.md`** - Detailed documentation with diagrams and examples
- **`README.md`** - This file - quick start and usage guide

---

**Transform competitive intelligence from manual research into automated, comprehensive analysis in minutes rather than weeks.**
#   C O M P E T I T O R - A N A L Y S I S - A G E N T  
 