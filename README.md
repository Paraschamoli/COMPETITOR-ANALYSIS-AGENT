# Local Business Competitor Analysis Agent

A production-grade AI system for comprehensive competitive intelligence analysis of local businesses. The agent analyzes competitors across multiple dimensions including products, pricing, SEO, social media, customer feedback, and strategic positioning.

## Features

- **Universal Business Support**: Works for ANY business type (restaurants, cafes, shops, services, etc.)
- **7-Step Sequential Analysis**: Comprehensive coverage of all competitive dimensions
- **Data-Driven Reports**: Uses verified data sources, no invented information
- **Multi-Platform Intelligence**: Google Maps, Yelp, TripAdvisor, social media platforms
- **Advanced Sections**: Customer personas, risk assessment, financial benchmarks (optional)
- **Google Maps Scraper**: Docker-based integration for accurate review data (optional)

## Quick Start

### Prerequisites

- Python 3.8+
- OpenRouter API key
- Optional: Docker (for Google Maps Scraper)
- Optional: Agent Reach CLI tools (for enhanced platform access)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "COMPETITOR ANALYSIS AGENT"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Required Environment Variables

Create a `.env` file with:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-api-key
TAVILY_API_KEY=tvly-your-tavily-api-key
SERPER_API_KEY=your-serper-api-key
FIRECRAWL_API_KEY=fc-your-firecrawl-api-key

# Optional (but recommended)
ENABLE_ADVANCED_SECTIONS=true
ENABLE_VISUAL_CHARTS=true
STRICT_VERIFICATION=true

# Optional - Google Maps Scraper (requires Docker)
ENABLE_GOOGLE_MAPS_SCRAPER=true

# Optional - YouTube API
YOUTUBE_API_KEY=your-youtube-api-key
```

## Usage

### Basic Analysis

```bash
python main_modular.py --company "Foodhallen" --domain "food hall" --location "Amsterdam"
```

### With Initial Competitors

```bash
python main_modular.py --company "Cafe de Klos" \
                       --domain "cafe" \
                       --location "Amsterdam" \
                       --initial_competitors "De Bolhoed, Cafe de Paris"
```

### Custom Output Path

```bash
python main_modular.py --company "Restaurant De Kas" \
                       --domain "restaurant" \
                       --location "Amsterdam" \
                       --output "./reports/analysis.md"
```

## Command Line Options

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--company` | Yes | Target business name | `"Foodhallen"` |
| `--domain` | Yes | Business type/category | `"cafe"`, `"restaurant"`, `"shop"`, `"service"` |
| `--location` | Yes | Geographic location | `"Amsterdam"`, `"New York"` |
| `--initial_competitors` | No | Starting competitors | `"Competitor1, Competitor2"` |
| `--output` | No | Custom output file path | `"./reports/analysis.md"` |

## Supported Business Types

The agent works with ANY business type:

- **Food & Beverage**: Restaurants, cafes, bars, food halls
- **Retail**: Shops, boutiques, stores, markets
- **Services**: Gyms, salons, professional services, healthcare
- **Entertainment**: Venues, theaters, clubs
- **Real Estate**: Agencies, property management
- **Professional**: Consulting, legal, financial services
- And more...

## Analysis Pipeline

### Step 1: Competitor Discovery
- Auto-discovers 6-10 competitors using multiple sources
- Filters out irrelevant competitors (internal vendors, wrong-city venues, low-review competitors)
- Extracts competitor count for data-driven reporting

### Step 2: Product & Service Analysis
- Deep-dive into offerings, facilities, operations
- Verifies accessibility features (doesn't assume)
- Analyzes all discovered competitors

### Step 3: Pricing & Business Model
- Extracts pricing information and business models
- Analyzes delivery platform presence (Uber Eats, Deliveroo, Thuisbezorgd)
- Competitive positioning analysis

### Step 4: Local SEO & Content Strategy
- Google Maps ranking and optimization
- Local citations and business listings
- Content strategy recommendations

### Step 5: Social Media Intelligence
- Platform presence and engagement analysis
- Enhanced data via Agent Reach (when available)
- Community engagement assessment

### Step 6: Local News & Market Intelligence
- Recent developments and events (3-6 months)
- Awards, partnerships, business updates
- Local media coverage analysis

### Step 7: Customer Feedback Analysis
- Multi-platform review aggregation
- Sentiment analysis with verified quotes
- Single source of truth for review counts

### Bonus: SWOT Analysis & Strategic Recommendations
- Data-driven SWOT analysis using actual competitor count
- Strategic recommendations based on all research

### Optional: Advanced Sections
When enabled via `ENABLE_ADVANCED_SECTIONS=true`:

1. Customer Personas (data-driven only)
2. Risk Assessment (with source citations)
3. Actionable Recommendations
4. Financial Benchmarks (with source citations)
5. Digital Ads & Paid Media analysis
6. UGC & Hashtag Analysis
7. Accessibility & Inclusivity (verified only)
8. Seasonal Trends (with source citations)
9. Next Steps / Action Plan

## Output

### Report Structure

Generated reports include:

1. **Executive Summary** (data-driven with actual metrics)
2. **Competitive Landscape Overview** (with comparison matrix)
3. **Product & Feature Analysis**
4. **Pricing & Business Models**
5. **SEO & Content Strategy**
6. **Social Media Intelligence**
7. **News & Recent Developments**
8. **Customer Feedback Analysis**
9. **SWOT Analysis & Strategic Recommendations**
10. **Advanced Sections** (if enabled)

### File Format

- **Format**: Markdown (.md)
- **Location**: `./output/` directory (auto-created)
- **Naming**: `competitor_analysis_{company}_{domain}_{timestamp}.md`
- **Encoding**: UTF-8

## Optional Integrations

### Google Maps Scraper (Docker Required)

For more accurate review data:

1. Install and run Docker Desktop
2. Set `ENABLE_GOOGLE_MAPS_SCRAPER=true` in `.env`
3. The scraper provides:
   - Exact review counts and ratings
   - 33+ data points per business
   - Coordinates and business status
   - 30-second timeout to prevent hanging

### Agent Reach (Enhanced Platform Access)

For direct platform data access:

1. Install Agent Reach CLI tools
2. Enhanced data from:
   - Twitter/X (real tweets, engagement)
   - Reddit (discussions, sentiment)
   - GitHub (repository activity)

### Crawl4AI (Alternative Scraper)

Free, open-source alternative to Firecrawl:
- JavaScript rendering capability
- Anti-bot evasion
- No API key required

## Configuration Options

### Environment Variables

```bash
# Advanced Features
ENABLE_ADVANCED_SECTIONS=true     # Generate advanced strategic sections
ENABLE_VISUAL_CHARTS=true          # ASCII charts in reports
STRICT_VERIFICATION=true           # Reject unverified data

# Google Maps Scraper
ENABLE_GOOGLE_MAPS_SCRAPER=true    # Enable Docker-based scraper

# Model Configuration (optional)
COORDINATOR_MODEL=openai/gpt-4.1
AGENT_MODEL=openai/gpt-4.1-mini
```

## Performance

- **Report Size**: 40,000+ characters
- **Execution Time**: 3-5 minutes
- **Competitor Coverage**: 6-10 competitors
- **Data Sources**: 8+ platforms analyzed
- **Success Rate**: 95%+ with fallbacks

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify OpenRouter API key is valid
   - Check key format: `sk-or-v1-...`

2. **Docker Issues**
   - Ensure Docker Desktop is running
   - Check if port 2375 is available

3. **Missing Data**
   - Some businesses have limited public data
   - System marks as "Unable to verify" when data unavailable

4. **Timeout Issues**
   - Google Maps Scraper uses 30-second timeout
   - Network issues may cause timeouts

### Debug Mode

Enable verbose logging:
```bash
export PYTHONPATH=.
python main_modular.py --company "Test" --domain "restaurant" --location "Amsterdam" 2>&1 | tee debug.log
```

## Examples

### Restaurant Analysis
```bash
python main_modular.py --company "Restaurant De Kas" \
                       --domain "restaurant" \
                       --location "Amsterdam"
```

### Cafe Analysis
```bash
python main_modular.py --company "Cafe de Klos" \
                       --domain "cafe" \
                       --location "Amsterdam" \
                       --initial_competitors "De Bolhoed, Cafe de Paris"
```

### Service Business Analysis
```bash
python main_modular.py --company "Fitness First" \
                       --domain "gym" \
                       --location "Amsterdam"
```

## Architecture

### System Components

- **Core**: Sequential 7-step pipeline with shared_data
- **Agents**: 9 specialized agents for different analysis dimensions
- **Tools**: Search engines, web scrapers, platform integrations
- **Models**: OpenRouter GPT-4.1 (coordinator) and GPT-4.1-mini (agents)

### Data Flow

```
User Input
    |
    v
Competitor Discovery (extract competitor_count)
    |
    v
Product Analysis
    |
    v
Pricing Analysis
    |
    v
SEO Analysis
    |
    v
Social Media Analysis
    |
    v
News Analysis
    |
    v
Customer Feedback (extract google_reviews)
    |
    v
SWOT Analysis (uses competitor_count)
    |
    v
Advanced Sections (data-only)
    |
    v
Report Generation (uses shared_data)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Documentation**: See `specs.md` for comprehensive technical specifications
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions

## Changelog

### Version 1.0.0 (April 13, 2026)
- Initial release with 7-step sequential analysis
- Universal business type support
- Google Maps Scraper integration (opt-in)
- Advanced sections with data-only requirements
- Full competitor coverage enforcement
- Data-driven Executive Summary
- Accessibility verification requirements
- Quote verification (no "derived from analysis")
- Source citation requirements for seasonal/financial data

---

**Generated by Competitor Analysis Agent Team**  
*Last updated: April 13, 2026*
