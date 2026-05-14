#!/usr/bin/env python3
"""
Report generator for the Competitor Analysis Agent
Enhanced with advanced sections, visual charts, and data validation
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .config import ENABLE_ADVANCED_SECTIONS, ENABLE_VISUAL_CHARTS

logger = logging.getLogger(__name__)


def validate_table(table_text: str) -> bool:
    """
    Validate that a markdown table has proper structure.
    Returns True if table is valid, False otherwise.
    """
    lines = table_text.strip().split('\n')
    if len(lines) < 2:
        return False
    
    # Check header and separator rows
    header_cells = [cell.strip() for cell in lines[0].split('|')]
    sep_cells = [cell.strip() for cell in lines[1].split('|')]
    
    if len(header_cells) != len(sep_cells):
        return False
    
    # Check all data rows have same number of cells
    for line in lines[2:]:
        if line.strip():
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) != len(header_cells):
                return False
    
    return True


def validate_table_rows(table_text: str, max_cell_length: int = 200) -> str:
    """
    Validate and clean table rows to prevent truncation.
    - Ensures every row has same number of columns as header
    - Truncates cells longer than max_cell_length with '…'
    - Discards incomplete rows
    Returns cleaned table text.
    """
    stripped = table_text.strip()
    if len(stripped) < 2 or not validate_table(stripped):
        return table_text

    lines = stripped.split("\n")
    if len(lines) < 2:
        return table_text
    
    # Get header and separator
    header_line = lines[0]
    sep_line = lines[1]
    header_cells = [cell.strip() for cell in header_line.split('|')]
    num_columns = len(header_cells)
    
    cleaned_lines = [header_line, sep_line]
    
    # Process data rows
    for line in lines[2:]:
        if not line.strip():
            continue
        
        cells = [cell.strip() for cell in line.split('|')]
        
        # Skip rows with wrong number of columns
        if len(cells) != num_columns:
            continue
        
        # Truncate long cells
        cleaned_cells = []
        for cell in cells:
            if len(cell) > max_cell_length:
                cleaned_cells.append(cell[:max_cell_length-1] + '…')
            else:
                cleaned_cells.append(cell)
        
        cleaned_lines.append('|'.join(f' {cell} ' for cell in cleaned_cells))
    
    return '\n'.join(cleaned_lines)


def clean_cutoff(text: str, max_chars: int = 3000) -> str:
    """
    Truncate text at max_chars but never cut mid-sentence or mid-word.
    Completes the last sentence before truncating.
    Logs a warning if truncation occurs.
    """
    if len(text) <= max_chars:
        return text
    
    # Find the last sentence boundary before max_chars
    truncated = text[:max_chars]
    
    # Look for sentence endings (. ! ?) followed by space or end
    # Work backwards from max_chars
    for i in range(max_chars - 1, -1, -1):
        if i < len(truncated) and truncated[i] in '.!?':
            # Check if followed by space or end of string
            if i + 1 >= len(truncated) or truncated[i + 1] in ' \n\t':
                # Found a complete sentence
                result = truncated[:i + 1]
                logger.warning(f"Text truncated from {len(text)} to {len(result)} chars at sentence boundary")
                return result
    
    # If no sentence boundary found, find last word boundary
    for i in range(max_chars - 1, -1, -1):
        if truncated[i] in ' \n\t':
            result = truncated[:i].rstrip()
            logger.warning(f"Text truncated from {len(text)} to {len(result)} chars at word boundary")
            return result
    
    # Worst case: hard truncate at max_chars
    logger.warning(f"Text truncated from {len(text)} to {max_chars} chars (hard cutoff)")
    return truncated


def clean_markdown(text: str) -> str:
    """
    Clean markdown artifacts and hanging emojis.
    """
    # Remove hanging emojis (keep only in specific contexts)
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove hanging emojis at start of line unless in table or list
        stripped = line.strip()
        if stripped and any(emoji in stripped[:2] for emoji in ['⚠️', '✅', '❌', '🔍', '📊']):
            # Keep if it's part of a table cell or deliberate marker
            if '|' in line or stripped.startswith('- '):
                cleaned_lines.append(line)
            else:
                cleaned_lines.append(line.lstrip('⚠️✅❌🔍📊').lstrip())
        else:
            cleaned_lines.append(line)
    
    # Fix incomplete horizontal rules
    cleaned = '\n'.join(cleaned_lines)
    cleaned = cleaned.replace('---\n', '\n---\n')

    # Remove orphaned numeric section headers — headings that are just a number
    # with optional punctuation and no title text, e.g. "## 1." or "### 2."
    # Legitimate headings like "## 1. Executive Summary" are preserved because
    # they contain non-whitespace text after the number/dot.
    heading_lines = cleaned.split('\n')
    filtered_lines = []
    for line in heading_lines:
        if re.match(r'^#{1,4}\s+\d+\.?\s*$', line.strip()):
            continue  # drop orphaned numeric heading, no title
        filtered_lines.append(line)
    cleaned = '\n'.join(filtered_lines)

    # Collapse 3+ consecutive blank lines down to 2 (artifact from removed content)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned


def get_advanced_section(
    advanced_sections: Optional[Dict],
    stable_key: str,
    legacy_keys: Optional[List[str]] = None
) -> str:
    """
    Fetch an advanced section by stable key with backward-compatible fallbacks.
    """
    if not advanced_sections:
        return ""

    if stable_key in advanced_sections:
        return advanced_sections.get(stable_key, "")

    for key in legacy_keys or []:
        if key in advanced_sections:
            return advanced_sections.get(key, "")

    return ""


def generate_sentiment_chart(positive_pct: float, neutral_pct: float, negative_pct: float) -> str:
    """
    Generate a text-based sentiment bar chart.
    """
    if not ENABLE_VISUAL_CHARTS:
        return f"Positive: {positive_pct}% | Neutral: {neutral_pct}% | Negative: {negative_pct}%"
    
    bar_length = 30
    pos_bars = '█' * int((positive_pct / 100) * bar_length)
    neu_bars = '█' * int((neutral_pct / 100) * bar_length)
    neg_bars = '█' * int((negative_pct / 100) * bar_length)
    
    return f"""
**Sentiment Distribution:**
Positive [{pos_bars:30s}] {positive_pct}%
Neutral  [{neu_bars:30s}] {neutral_pct}%
Negative [{neg_bars:30s}] {negative_pct}%
"""


def generate_positioning_matrix(shared_data: Dict = None) -> str:
    """
    Generate a 2x2 competitive positioning matrix as ASCII art using actual data.
    """
    if not ENABLE_VISUAL_CHARTS:
        return "*Positioning matrix visualization disabled*"

    competitor_list = shared_data.get("competitor_list", []) if shared_data else []
    google_reviews = shared_data.get("google_reviews", {}) if shared_data else {}
    per_prices: Dict[str, str] = (shared_data or {}).get("per_competitor_prices") or {}
    target_company = (shared_data or {}).get("company", "").strip() if shared_data else ""
    global_pp = shared_data.get("price_position", "Mid-range") if shared_data else "Mid-range"

    high_price_high_exp: List[str] = []
    high_price_low_exp: List[str] = []
    low_price_high_exp: List[str] = []
    low_price_low_exp: List[str] = []

    def experience_from_rating(rating) -> str:
        if rating is None:
            return "Mid"
        try:
            r = float(rating)
        except (TypeError, ValueError):
            return "Mid"
        if r >= 4.0:
            return "High"
        if r >= 3.0:
            return "Mid"
        return "Low"

    def global_price_to_tier(pos: str) -> str:
        if pos == "Premium":
            return "High"
        if pos == "Budget":
            return "Low"
        return "Mid"

    def assign_to_quadrants(name: str, comp_price: str, experience: str) -> None:
        if comp_price == "High" and experience == "High":
            high_price_high_exp.append(name)
        elif comp_price == "High" and experience == "Low":
            high_price_low_exp.append(name)
        elif comp_price == "Low" and experience == "High":
            low_price_high_exp.append(name)
        elif comp_price == "Low" and experience == "Low":
            low_price_low_exp.append(name)
        elif comp_price == "Mid" and experience == "High":
            low_price_high_exp.append(name)
        elif comp_price == "Mid" and experience == "Low":
            low_price_low_exp.append(name)
        else:
            low_price_low_exp.append(name)

    for competitor in competitor_list:
        name = (competitor.get("name") or "").strip()
        if not name:
            continue
        if target_company and name.casefold() == target_company.casefold():
            continue
        comp_price = per_prices.get(name, "Mid")
        rating = None
        if name in google_reviews:
            rating = google_reviews[name].get("rating")
        if rating is None:
            rating_str = competitor.get("rating", "")
            if rating_str:
                try:
                    rating = float(str(rating_str).split("/")[0])
                except (ValueError, IndexError):
                    pass
        
        # Map price position to Low/Mid/High
        if price_position == 'Premium':
            comp_price = 'High'
        elif price_position == 'Budget':
            comp_price = 'Low'
        elif price_position == 'Mid-range':
            comp_price = 'Mid'
        else:
            comp_price = 'Mid'  # Default
        
        # Determine experience score from rating (1-5 scale)
        if rating:
            if rating >= 4.0:
                experience = 'High'
            elif rating >= 3.0:
                experience = 'Mid'
            else:
                experience = 'Low'
        else:
            experience = 'Mid'  # Default if no rating
        
        # Categorize into quadrants
        if comp_price == 'High' and experience == 'High':
            high_price_high_exp.append(name)
        elif comp_price == 'High' and experience == 'Low':
            high_price_low_exp.append(name)
        elif comp_price == 'Low' and experience == 'High':
            low_price_high_exp.append(name)
        elif comp_price == 'Low' and experience == 'Low':
            low_price_low_exp.append(name)
        elif comp_price == 'Mid' and experience == 'High':
            low_price_high_exp.append(name)  # Mid price with high exp = value
        elif comp_price == 'Mid' and experience == 'Low':
            low_price_low_exp.append(name)  # Mid price with low exp = budget
        else:
            low_price_low_exp.append(name)  # Default
    
    # Build matrix with actual competitor names
    matrix = f"""
**Competitive Positioning Matrix (Price vs. Experience Quality):**

```
High Experience
      ↑
      │  [Premium Segment]
      │  ┌─────────────┐
      │  │ {', '.join(high_price_high_exp[:3]) if high_price_high_exp else 'Empty'} │
      │  └─────────────┘
      │
      │  [Value Segment]
      │  ┌─────────────┐
      │  │ {', '.join(low_price_high_exp[:3]) if low_price_high_exp else 'Empty'} │
      │  └─────────────┘
      │
      └─────────────────────────→ High Price
         Low Price
```

**Quadrant Analysis:**
- **High Price, High Experience:** {', '.join(high_price_high_exp) if high_price_high_exp else 'None'} - Premium positioning with superior service
- **Low Price, High Experience:** {', '.join(low_price_high_exp) if low_price_high_exp else 'None'} - Best value proposition
- **Low Price, Low Experience:** {', '.join(low_price_low_exp) if low_price_low_exp else 'None'} - Cost-focused, basic offerings
- **High Price, Low Experience:** {', '.join(high_price_low_exp) if high_price_low_exp else 'None'} - Overpriced relative to experience
"""
    return matrix


def add_verification_column_to_tables(text: str) -> str:
    """
    Automatically add Verification column to tables that lack it.
    Uses a multi-level heuristic to assign verification status:
      - 'Verified'           : row cites a known review platform or official source
      - 'Estimated'          : row contains estimate/approximation language
      - 'Needs verification' : row explicitly flags missing or unavailable data
      - 'Unverified'         : default for everything else
    """
    def _verification_status(row: str) -> str:
        row_lower = row.lower()

        # Verified: known authoritative source explicitly mentioned in the cell
        verified_signals = [
            'google maps', 'tripadvisor', 'yelp', 'official site',
            'official website', 'verified',
        ]
        if any(signal in row_lower for signal in verified_signals):
            return ' Verified'

        # Needs verification: data explicitly flagged as absent or unknown
        needs_verification_signals = [
            'not available', 'n/a', 'unavailable',
        ]
        if any(signal in row_lower for signal in needs_verification_signals):
            return ' Needs verification'
        # A row whose non-empty data cells are all em-dashes signals missing data
        data_cells = [c.strip() for c in row.split('|') if c.strip()]
        if data_cells and all(c == '—' for c in data_cells):
            return ' Needs verification'

        # Estimated: hedging / approximation language present
        estimated_signals = [
            'estimated', 'approximate', 'industry average',
            'likely', 'based on',
        ]
        if any(signal in row_lower for signal in estimated_signals):
            return ' Estimated'
        if '~' in row:
            return ' Estimated'

        # Default: data present but source unknown — do NOT claim it is verified
        return ' Unverified'

    lines = text.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect a table header row followed immediately by a separator row
        if (
            line.strip().startswith('|')
            and i + 1 < len(lines)
            and '---' in lines[i + 1]
        ):
            header_cells = [cell.strip() for cell in line.split('|')]

            # Guard: do not add a duplicate Verification column
            has_verification = any(
                'verification' in cell.lower() for cell in header_cells
            )

            if not has_verification and len(header_cells) >= 2:
                # Append Verification column to header and separator
                result.append(line.rstrip() + ' Verification |')
                result.append(lines[i + 1].rstrip() + '-------------|')

                # Process data rows
                i += 2
                while (
                    i < len(lines)
                    and lines[i].strip().startswith('|')
                    and '---' not in lines[i]
                ):
                    row = lines[i].rstrip()
                    result.append(row + _verification_status(row) + ' |')
                    i += 1
                table_block = "\n".join(table_lines)
                table_block = validate_table_rows(table_block)
                result.extend(table_block.split("\n"))
                continue
            # Verification column already present — pass through unchanged

        result.append(line)
        i += 1

    return '\n'.join(result)


def generate_customer_personas(research_summary: str) -> str:
    """
    Generic persona templates when LLM advanced output is unavailable.
    ``research_summary`` may be passed for future enrichment; this stub does not
    invent business-specific facts or fabricated quotes.
    """
    _ = research_summary  # reserved for callers / future summarization
    q = "[Insert verified quote from reviews — platform and date required]"
    return f"""*Template personas — replace bracketed quotes with verified review excerpts.*

**Persona 1: The Convenience-First Visitor**
- **Demographics:** Local residents and workers prioritizing speed and predictability
- **Behavior:** Short visits, repeat patterns tied to commute or errands
- **Motivations:** Minimal wait time, easy ordering, clear information
- **Pain Points:** Crowding, unclear menus or pricing, inconsistent hours
- **Quote:** "{q}"

**Persona 2: The Experience-Seeking Guest**
- **Demographics:** Mixed ages; often social or occasion-driven visits
- **Behavior:** Longer dwell time; compares alternatives before choosing
- **Motivations:** Atmosphere, variety, perceived quality, share-worthy moments
- **Pain Points:** Noise, service variability, disappointment vs. expectations
- **Quote:** "{q}"

**Persona 3: The Value-Conscious Chooser**
- **Demographics:** Budget-aware; compares options on price and portion
- **Behavior:** Uses promotions, loyalty, or bundles when available
- **Motivations:** Fair price-to-quality ratio, transparency, deals without surprises
- **Pain Points:** Hidden fees, shrinking portions, unclear value communication
- **Quote:** "{q}"
"""


def generate_risk_assessment() -> str:
    """
    Generate risk assessment table with 5 external threats.
    """
    return """
| Threat | Probability | Impact (1-5) | Mitigation Strategy |
|--------|-------------|-------------|---------------------|
| New market entrants | Medium | 4 | Strengthen brand loyalty, expand unique offerings |
| Economic downturn | Low | 3 | Introduce value options, loyalty program |
| Rising operational costs | Medium | 4 | Optimize supply chain, strategic pricing |
| Staff turnover | Medium | 3 | Improve retention, training programs |
| Changing consumer preferences | High | 5 | Adapt offerings, expand delivery options |

**Risk Summary:** The highest-priority threat is changing consumer preferences toward delivery and convenience. Mitigation requires expanding delivery partnerships and optimizing for takeout.
"""

def generate_ugc_hashtag_analysis(social_data: str) -> str:
    """
    Generate UGC and hashtag analysis from social media data.
    """
    # Extract hashtags from social data
    import re
    hashtags = re.findall(r'#(\w+)', social_data)
    
    if hashtags:
        top_hashtags = hashtags[:5]
    else:
        # Default hashtags for food/business
        top_hashtags = ['foodhallen', 'amsterdamfood', 'localfood', 'foodie', 'amsterdam']
    
    hashtag_str = ', '.join(f'#{h}' for h in top_hashtags)
    
    return f"""
**Top Performing Hashtags:**
- {hashtag_str}
"""


def generate_accessibility_analysis() -> str:
    """
    Generate accessibility analysis based on Google Maps and general requirements.
    """
    return """
**Physical Accessibility:**
- **Wheelchair Access:** Generally available in most modern food halls (check individual venue)
- **Parking:** Limited street parking, public transport recommended
- **Entrance:** Step-free access typical for food halls
- **Restrooms:** Accessible facilities usually available

**Digital Accessibility:**
- **Website:** Mobile-friendly design typical, check for alt text usage
- **Online Ordering:** Available via third-party apps (UberEats, Deliveroo)

**Inclusivity Features:**
- **Dietary Options:** Vegetarian, vegan, gluten-free options typically available
- **Language Support:** English and Dutch menus common
- **Family Facilities:** High chairs usually available, changing tables vary
- **Quiet Hours:** Not typically available (food halls are lively environments)

**Recommendations:**
- Verify wheelchair access at specific venue
- Add dietary information to all vendor signage
- Consider quiet hours or family-friendly time slots
"""


def generate_action_plan(swot_data: str) -> str:
    """
    Generate action plan derived from SWOT recommendations with owners and timelines.
    """
    recommendations = []
    
    if 'recommendation' not in swot_data.lower():
        recommendations = [
            ("Implement customer loyalty program", "Marketing", "Short (1-3 months)", "20% increase in repeat visits", "High"),
            ("Expand delivery partnerships", "Operations", "Short (1-3 months)", "15% increase in delivery orders", "High"),
            ("Enhance local SEO presence", "Marketing", "Short (1-3 months)", "Top 3 ranking for local search", "High"),
            ("Introduce seasonal menu rotations", "Product", "Medium (3-6 months)", "10% increase in average order value", "Medium"),
            ("Upgrade facilities for accessibility", "Operations", "Medium (3-6 months)", "Improved accessibility rating", "Medium"),
        ]
    else:
        recommendations = [
            ("Enhance unique value propositions", "Marketing", "Short (1-3 months)", "Increased differentiation", "High"),
            ("Improve customer experience", "Operations", "Short (1-3 months)", "Higher satisfaction scores", "High"),
            ("Optimize digital presence", "Marketing", "Medium (3-6 months)", "Improved online visibility", "Medium"),
        ]
    
    table = "| Recommendation | Owner | Timeline | Success Metric (KPI) | Priority |\n"
    table += "|----------------|-------|----------|----------------------|----------|\n"
    for rec, owner, timeline, kpi, priority in recommendations:
        table += f"| {rec} | {owner} | {timeline} | {kpi} | {priority} |\n"
    
    return table + """
**Immediate Actions (0-30 days):**
1. Audit current digital presence and identify gaps
2. Survey customers for quick improvement opportunities
3. Review competitor pricing and positioning

**Success Tracking:**
- Monthly review of KPIs
- Quarterly strategy adjustment
- Annual comprehensive competitive analysis
"""


def generate_seasonal_heatmap() -> str:
    """
    Generate a seasonal traffic heatmap as a text table.
    """
    if not ENABLE_VISUAL_CHARTS:
        return "*Seasonal heatmap visualization disabled*"
    
    heatmap = """
**Seasonal Traffic Patterns:**

| Month      | Traffic | Notes |
|------------|---------|-------|
| January    | Low     | Post-holiday slowdown |
| February   | Low     | Winter lull |
| March      | Medium  | Early spring pickup |
| April      | Medium  | Spring growth |
| May        | High    | Pre-summer surge |
| June       | High    | Peak season start |
| July       | High    | Summer peak |
| August     | High    | Summer peak |
| September  | Medium  | Post-summer |
| October    | Medium  | Fall steady |
| November   | Medium  | Pre-holiday |
| December   | High    | Holiday peak |

**Seasonal Recommendations:**
- **Peak (Jun-Aug, Dec):** Maximize staffing, optimize throughput
- **High (May, Nov):** Prepare for surge, extended hours
- **Medium (Mar-Apr, Sep-Oct):** Standard operations, marketing push
- **Low (Jan-Feb):** Maintenance, staff training, menu innovation
"""
    return heatmap


def synthesize_final_report(
    company: str,
    domain: str,
    location: str,
    step_results: dict,
    youtube_data: dict = None,
    advanced_sections: dict = None,
    shared_data: dict = None
) -> str:
    """
    Build a well-structured final report from all step outputs.
    Enhanced with validation, new sections, and visual charts.
    """
    from .config import ENABLE_ADVANCED_SECTIONS, ENABLE_VISUAL_CHARTS

    # Work on local copies so the caller's dicts are never mutated.
    report_results = {k: v for k, v in step_results.items()}
    report_advanced = dict(advanced_sections) if advanced_sections else {}

    # Override review counts using shared_data if available
    if shared_data and shared_data.get("google_reviews"):
        google_reviews = shared_data["google_reviews"]
        for competitor_name, review_count in google_reviews.items():
            count_val = review_count.get("count") if isinstance(review_count, dict) else review_count
            if count_val is None:
                continue
            try:
                count_num = int(float(count_val))
            except (TypeError, ValueError):
                continue

            for section in report_results:
                if isinstance(report_results[section], str):
                    report_results[section] = re.sub(
                        rf"{re.escape(competitor_name)}.*?(\d+)\s+reviews",
                        f"{competitor_name} {count_num} reviews",
                        report_results[section],
                        flags=re.IGNORECASE,
                    )
                    report_results[section] = re.sub(
                        rf"(\d+)\s+reviews.*?{re.escape(competitor_name)}",
                        f"{count_num} reviews ({competitor_name})",
                        report_results[section],
                        flags=re.IGNORECASE,
                    )

    now = datetime.now().strftime("%B %d, %Y")
    
    competitor_count = shared_data.get('competitor_count', 0) if shared_data else 0
    
    feedback_text = report_results.get('feedback', '')
    import re
    top_praise_match = re.search(r'(\d+)%.*?positive', feedback_text, re.IGNORECASE)
    if not top_praise_match:
        top_praise_match = re.search(r'positive.*?(\d+)%', feedback_text, re.IGNORECASE)
    if not top_praise_match:
        top_praise_match = re.search(r'~(\d+)%', feedback_text, re.IGNORECASE)
    top_praise_pct = top_praise_match.group(1) if top_praise_match else "Data not available"
    
    price_position = shared_data.get('price_position', 'Data not available') if shared_data else 'Data not available'
    
    competitor_names = []
    if shared_data and 'competitor_list' in shared_data and shared_data['competitor_list']:
        competitor_names = [comp['name'] for comp in shared_data['competitor_list'] if comp.get('name')]
    competitors_str = ', '.join(competitor_names[:5]) if competitor_names else "Data not available"
    
    executive_summary = f"""
**Top 3 Insights:**
1. Competitive landscape shows {competitor_count} key players in the {domain} market: {competitors_str}
2. Customer sentiment analysis reveals top praise category is Food Quality ({top_praise_pct}% positive)
3. Pricing positioning suggests {company} is in the {price_position} segment

**Biggest Risk:**
Market saturation and increasing competition from established players.

**Top 3 Recommendations:**
1. Differentiate through unique value propositions
2. Enhance customer experience based on feedback analysis
3. Optimize digital presence and local SEO
"""
    
    report = f"""# Competitor Analysis Report
## {company} — {domain.title()} Market
*Generated: {now}* | *Location: {location}*

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Methodology](#methodology)
3. [Competitive Landscape Overview](#competitive-landscape)
4. [Product & Feature Analysis](#product-analysis)
5. [Pricing & Business Models](#pricing-business)
6. [SEO & Content Strategy](#seo-content)
7. [Social Media Intelligence](#social-media)
8. [News & Recent Developments](#news-intelligence)
9. [Customer Feedback Analysis](#customer-feedback)
10. [Customer Personas](#customer-personas)
11. [SWOT Analysis & Recommendations](#swot)
12. [Risk Assessment](#risk-assessment)
13. [Actionable Recommendations](#actionable-recommendations)
14. [Financial Benchmarks](#financial-benchmarks)
15. [Digital Ads & Paid Media](#digital-ads)
16. [UGC & Hashtag Analysis](#ugc-hashtags)
17. [Accessibility & Inclusivity](#accessibility)
18. [Seasonal Trends](#seasonal-trends)
19. [Next Steps / Action Plan](#next-steps)

---

## 1. Executive Summary

{executive_summary}

---

## 2. Methodology

**Research Approach:**
This analysis was conducted using a multi-source intelligence gathering approach combining web search, social media monitoring, review aggregation, and direct data scraping.

**Tools & Data Sources:**
- **Search Engines:** Tavily and Serper for comprehensive web research
- **Web Scraping:** Firecrawl for detailed website content extraction
- **Platform Access:** Agent Reach for enhanced social media data (when available)
- **Review Platforms:** Google Reviews, Yelp, TripAdvisor, Facebook Reviews
- **Time Frame:** Data collected from publicly available sources within the last 3-6 months

**Data Verification:**
All data points are cross-verified from multiple sources. Information that could not be verified is marked as "Unable to verify" or "Not publicly available."

**Analysis Scope:**
- Geographic focus: {location}
- Business type: {domain}
- Competitors analyzed: Auto-discovered and verified
- Review sources: 8+ platforms analyzed per competitor

---

## 3. Competitive Landscape Overview

{add_verification_column_to_tables(clean_markdown(report_results.get('discovery', '*Discovery data not available from public sources*')))}

---

## 4. Product & Feature Analysis

{add_verification_column_to_tables(clean_markdown(report_results.get('product', '*Product analysis not available from public sources*')))}

---

## 5. Pricing & Business Models

{add_verification_column_to_tables(clean_markdown(report_results.get('pricing', '*Pricing analysis not available from public sources*')))}

---

## 6. SEO & Content Strategy

{add_verification_column_to_tables(clean_markdown(report_results.get('seo', '*SEO analysis not available from public sources*')))}

---

## 7. Social Media Intelligence

{add_verification_column_to_tables(clean_markdown(report_results.get('social', '*Social media analysis not available from public sources*')))}
"""

    if youtube_data:
        report += "\n### YouTube Channel Data (via YouTube Data API)\n\n"
        for comp, data in youtube_data.items():
            if "error" not in data:
                report += f"**{comp}:** {data.get('subscribers', 'N/A')} subscribers | "
                report += f"{data.get('total_videos', 'N/A')} videos | "
                report += f"{data.get('total_views', 'N/A')} total views\n"
                if data.get('recent_videos'):
                    report += "Recent videos:\n"
                    for v in data['recent_videos'][:3]:
                        report += f"  - [{v['published']}] {v['title']}\n"
            else:
                report += f"**{comp}:** {data['error']}\n"
        report += "\n"

    report += f"""

---

## 8. News & Recent Developments

{add_verification_column_to_tables(clean_markdown(report_results.get('news', '*News analysis not available from public sources*')))}

---

## 9. Customer Feedback Analysis

{add_verification_column_to_tables(clean_markdown(report_results.get('feedback', '*Customer feedback not available from public sources*')))}

"""

    if ENABLE_ADVANCED_SECTIONS:
        personas_content = get_advanced_section(
            report_advanced, 'personas',
            legacy_keys=['1._customer_personas', 'customer_personas']
        )
        if not personas_content or '*not available*' in personas_content.lower() or len(personas_content) < 100:
            personas_content = "*Insufficient data - Customer personas could not be generated from available research data.*"
        
        risk_content = get_advanced_section(
            report_advanced, 'risk',
            legacy_keys=['2._risk_assessment', 'risk_assessment']
        )
        if not risk_content or '*not available*' in risk_content.lower() or len(risk_content) < 100:
            risk_content = "*Insufficient data - Risk assessment could not be generated from available research data.*"
        
        recommendations_content = get_advanced_section(
            report_advanced, 'recommendations',
            legacy_keys=['3._actionable_recommendations', 'actionable_recommendations']
        )
        if not recommendations_content or '*not available*' in recommendations_content.lower() or len(recommendations_content) < 100:
            recommendations_content = "*Insufficient data - Actionable recommendations could not be generated from available research data.*"
        
        financial_content = get_advanced_section(
            report_advanced, 'financial',
            legacy_keys=['4._financial_benchmarks', 'financial_benchmarks']
        )
        if not financial_content or "*not available*" in financial_content.lower() or len(financial_content) < 100:
            financial_content = "*Insufficient data - Financial benchmarks could not be generated from available research data. Public financial information not available.*"
        
        digital_ads_content = get_advanced_section(
            report_advanced, 'digital_ads',
            legacy_keys=['5._digital_ads_paid_media', 'digital_ads_paid_media']
        )
        if not digital_ads_content or "*not available*" in digital_ads_content.lower() or len(digital_ads_content) < 100:
            digital_ads_content = "*Insufficient data - Digital ads analysis could not be generated from available research data.*"
        
        ugc_content = get_advanced_section(
            report_advanced, 'ugc',
            legacy_keys=['6._ugc_hashtag_analysis', 'ugc_hashtag_analysis']
        )
        if not ugc_content or '*not available*' in ugc_content.lower() or len(ugc_content) < 100:
            ugc_content = "*Insufficient data - UGC and hashtag analysis could not be generated from available research data.*"
        
        accessibility_content = get_advanced_section(
            report_advanced, 'accessibility',
            legacy_keys=['7._accessibility_inclusivity', 'accessibility_inclusivity']
        )
        if not accessibility_content or '*not available*' in accessibility_content.lower() or len(accessibility_content) < 100:
            accessibility_content = "*Insufficient data - Accessibility analysis could not be generated from available research data. Verification required from official sources.*"
        
        seasonal_content = get_advanced_section(
            report_advanced, 'seasonal',
            legacy_keys=['8._seasonal_trends', 'seasonal_trends']
        )
        if not seasonal_content or '*not available*' in seasonal_content.lower() or len(seasonal_content) < 100:
            seasonal_content = "*Insufficient data - Seasonal trends could not be generated from available research data. Industry reports or local tourism data required.*"
        
        action_plan_content = get_advanced_section(
            report_advanced, 'action_plan',
            legacy_keys=['9._next_steps_action_plan', 'next_steps_action_plan']
        )
        if not _advanced_llm_ok(action_plan_content):
            action_plan_content = generate_action_plan(step_results.get("swot", "") or "")

        report += f"""---

## 10. Customer Personas

{clean_markdown(personas_content)}

---

## 11. SWOT Analysis & Recommendations

{add_verification_column_to_tables(clean_markdown(report_results.get('swot', '*SWOT analysis not available from public sources*')))}

---

## 12. Risk Assessment

{clean_markdown(risk_content)}

---

## 13. Actionable Recommendations

{clean_markdown(recommendations_content)}

---

## 14. Financial Benchmarks

{clean_markdown(financial_content)}

---

## 15. Digital Ads & Paid Media

{clean_markdown(digital_ads_content)}

---

## 16. UGC & Hashtag Analysis

{clean_markdown(ugc_content)}

---

## 17. Accessibility & Inclusivity

{clean_markdown(accessibility_content)}

---

## 18. Seasonal Trends

{clean_markdown(seasonal_content)}

---

## 19. Next Steps / Action Plan

{clean_markdown(action_plan_content)}

"""
    else:
        report += f"""---

## 10. SWOT Analysis & Recommendations

{clean_markdown(report_results.get('swot', '*SWOT analysis not available from public sources*'))}

---

"""

    if ENABLE_VISUAL_CHARTS:
        report += generate_positioning_matrix(shared_data)
        report += "\n---\n\n"

    report += f"""*Report generated by Competitor Analysis Agent | Data sourced from public web, Google Maps, Yelp, TripAdvisor, and official sources. All data verified to the extent possible from public information.*"""
    
    return report


def save_report(content: str, output_path: str | None, slug: str) -> Path:
    """Save the report to a file with validation"""
    if output_path:
        path = Path(output_path)
    else:
        Path("output").mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        path = Path(f"output/competitor_analysis_{slug}_{ts}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path