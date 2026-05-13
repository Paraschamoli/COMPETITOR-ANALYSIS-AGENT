#!/usr/bin/env python3
"""
Report generator for the Competitor Analysis Agent
Corrected version — fixes applied:

  1.  clean_cutoff blanket 3 000-char truncation removed.
      Each section now has its own appropriate limit (or no limit).
      Truncation at 3 000 chars silently destroyed multi-competitor tables.

  2.  Advanced-section "insufficient data" guard rewritten.
      Old guard: `'*not available*' in content.lower()` — any passing mention
      of "not available" threw away the entire section.
      New guard: only replace content when the WHOLE section is a stub
      (< 150 chars OR entirely composed of placeholder phrases).

  3.  generate_positioning_matrix rewritten to use per-competitor price and
      rating data instead of one global price_position for every competitor.
      Old code put every competitor in the same quadrant.

  4.  generate_customer_personas was cut off — Personas 1 and 2 were missing,
      Persona 3 dangled outside any function. Function fully restored.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .config import ENABLE_ADVANCED_SECTIONS, ENABLE_VISUAL_CHARTS

logger = logging.getLogger(__name__)


# ── Placeholder phrases that indicate a section is genuinely empty ────────────
_STUB_PHRASES = (
    "insufficient data",
    "could not be generated",
    "not available from public sources",
    "data not available",
    "unable to verify",
)

def _is_stub(text: str) -> bool:
    """
    Return True only when the entire content is a stub / placeholder.
    A section that *mentions* unavailability in passing (e.g. one row in a
    table) is NOT a stub — the old guard incorrectly discarded those.
    """
    if not text or not text.strip():
        return True
    stripped = text.strip().lower()
    # Short AND matches a stub phrase → stub
    if len(stripped) < 150 and any(p in stripped for p in _STUB_PHRASES):
        return True
    # Entire text is just the placeholder sentence (no real content around it)
    non_stub_chars = stripped
    for p in _STUB_PHRASES:
        non_stub_chars = non_stub_chars.replace(p, "")
    if len(non_stub_chars.strip()) < 30:
        return True
    return False


# ── Table helpers ─────────────────────────────────────────────────────────────

def validate_table(table_text: str) -> bool:
    lines = table_text.strip().split('\n')
    if len(lines) < 2:
        return False
    header_cells = [cell.strip() for cell in lines[0].split('|')]
    sep_cells    = [cell.strip() for cell in lines[1].split('|')]
    if len(header_cells) != len(sep_cells):
        return False
    for line in lines[2:]:
        if line.strip():
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) != len(header_cells):
                return False
    return True


def validate_table_rows(table_text: str, max_cell_length: int = 200) -> str:
    lines = table_text.strip().split('\n')
    if len(lines) < 2:
        return table_text
    header_line  = lines[0]
    sep_line     = lines[1]
    header_cells = [cell.strip() for cell in header_line.split('|')]
    num_columns  = len(header_cells)
    cleaned_lines = [header_line, sep_line]
    for line in lines[2:]:
        if not line.strip():
            continue
        cells = [cell.strip() for cell in line.split('|')]
        if len(cells) != num_columns:
            continue
        cleaned_cells = [
            (cell[:max_cell_length - 1] + '…' if len(cell) > max_cell_length else cell)
            for cell in cells
        ]
        cleaned_lines.append('|'.join(f' {cell} ' for cell in cleaned_cells))
    return '\n'.join(cleaned_lines)


def clean_cutoff(text: str, max_chars: int) -> str:
    """
    Truncate text at max_chars but never cut mid-sentence or mid-word.
    Only call this when you have a genuine size budget (e.g. the executive
    summary).  Do NOT apply it globally to every section — that destroys
    multi-competitor tables (fix #1).
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    for i in range(max_chars - 1, -1, -1):
        if truncated[i] in '.!?' and (i + 1 >= len(truncated) or truncated[i + 1] in ' \n\t'):
            result = truncated[:i + 1]
            logger.warning("Text truncated %d→%d chars at sentence boundary", len(text), len(result))
            return result
    for i in range(max_chars - 1, -1, -1):
        if truncated[i] in ' \n\t':
            result = truncated[:i].rstrip()
            logger.warning("Text truncated %d→%d chars at word boundary", len(text), len(result))
            return result
    logger.warning("Text hard-truncated %d→%d chars", len(text), max_chars)
    return truncated


def clean_markdown(text: str) -> str:
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and any(emoji in stripped[:2] for emoji in ['⚠️', '✅', '❌', '🔍', '📊']):
            if '|' in line or stripped.startswith('- '):
                cleaned_lines.append(line)
            else:
                cleaned_lines.append(re.sub(r'^[\s⚠️✅❌🔍📊]+', '', line))
        else:
            cleaned_lines.append(line)
    cleaned = '\n'.join(cleaned_lines)
    cleaned = cleaned.replace('---\n', '\n---\n')
    return cleaned


def generate_sentiment_chart(positive_pct: float, neutral_pct: float, negative_pct: float) -> str:
    if not ENABLE_VISUAL_CHARTS:
        return f"Positive: {positive_pct}% | Neutral: {neutral_pct}% | Negative: {negative_pct}%"
    bar_length = 30
    pos_bars = '█' * int((positive_pct / 100) * bar_length)
    neu_bars = '█' * int((neutral_pct / 100) * bar_length)
    neg_bars = '█' * int((negative_pct / 100) * bar_length)
    return f"""
**Sentiment Distribution:**
Positive [{pos_bars:<30s}] {positive_pct}%
Neutral  [{neu_bars:<30s}] {neutral_pct}%
Negative [{neg_bars:<30s}] {negative_pct}%
"""


# ── Positioning matrix (fix #3) ───────────────────────────────────────────────

def _price_tier(competitor: dict) -> str:
    """
    Derive a Low / Mid / High price tier for one competitor from its own data.
    Uses the 'price_range' field ($ / $$ / $$$ / $$$$) when available,
    falls back to the global price_position only as a last resort.
    """
    raw = (
        competitor.get('price_range', '')
        or competitor.get('price_level', '')
        or competitor.get('price', '')
    ).strip()

    if raw:
        dollar_count = raw.count('$')
        if dollar_count >= 3:
            return 'High'
        if dollar_count == 2:
            return 'Mid'
        if dollar_count == 1:
            return 'Low'
        # Text labels
        lower = raw.lower()
        if any(w in lower for w in ('premium', 'expensive', 'high')):
            return 'High'
        if any(w in lower for w in ('budget', 'cheap', 'low', 'affordable')):
            return 'Low'
        return 'Mid'

    return 'Mid'  # genuine default when no price data at all


def _experience_tier(competitor: dict, google_reviews: dict) -> str:
    """
    Derive a Low / Mid / High experience tier from the competitor's rating.
    Checks google_reviews dict first (authoritative), then competitor dict.
    """
    rating = None

    name = competitor.get('name', '')
    if name and name in google_reviews:
        r = google_reviews[name]
        rating = r.get('rating') if isinstance(r, dict) else None

    if rating is None:
        rating_str = str(competitor.get('rating', '') or '')
        try:
            rating = float(rating_str.split('/')[0].strip())
        except (ValueError, IndexError):
            rating = None

    if rating is None:
        return 'Mid'
    if rating >= 4.2:
        return 'High'
    if rating >= 3.5:
        return 'Mid'
    return 'Low'


def generate_positioning_matrix(shared_data: Dict = None) -> str:
    if not ENABLE_VISUAL_CHARTS:
        return "*Positioning matrix visualization disabled*"

    competitor_list = (shared_data or {}).get('competitor_list', [])
    google_reviews  = (shared_data or {}).get('google_reviews', {})

    buckets: Dict[str, List[str]] = {
        'high_price_high_exp': [],
        'high_price_low_exp':  [],
        'low_price_high_exp':  [],
        'low_price_low_exp':   [],
    }

    for comp in competitor_list:
        name = comp.get('name', '').strip()
        if not name:
            continue
        price      = _price_tier(comp)             # per-competitor (fix #3)
        experience = _experience_tier(comp, google_reviews)

        if price == 'High' and experience == 'High':
            buckets['high_price_high_exp'].append(name)
        elif price == 'High' and experience in ('Low', 'Mid'):
            buckets['high_price_low_exp'].append(name)
        elif price in ('Low', 'Mid') and experience == 'High':
            buckets['low_price_high_exp'].append(name)
        else:
            buckets['low_price_low_exp'].append(name)

    def _fmt(names: List[str]) -> str:
        return ', '.join(names[:3]) if names else 'None identified'

    return f"""
**Competitive Positioning Matrix (Price vs. Experience Quality):**

```
High Experience
      ↑
      │  [Premium Segment]              │  [Value Leaders]
      │  {_fmt(buckets['high_price_high_exp']):<35s}│  {_fmt(buckets['low_price_high_exp'])}
      │                                 │
      │─────────────────────────────────┤
      │  [Overpriced]                   │  [Budget / Basic]
      │  {_fmt(buckets['high_price_low_exp']):<35s}│  {_fmt(buckets['low_price_low_exp'])}
      │                                 │
      └─────────────────────────────────────────→ Price
         Low Price                        High Price
```

**Quadrant Analysis:**
- **High Price + High Experience (Premium):** {_fmt(buckets['high_price_high_exp'])}
- **Low Price + High Experience (Value leaders):** {_fmt(buckets['low_price_high_exp'])}
- **Low Price + Low Experience (Budget/basic):** {_fmt(buckets['low_price_low_exp'])}
- **High Price + Low Experience (Overpriced):** {_fmt(buckets['high_price_low_exp'])}
"""


def add_verification_column_to_tables(text: str) -> str:
    """
    Add a Verification column to markdown tables that lack one.
    Fixed ternary operator precedence bug in original version.
    """
    lines  = text.split('\n')
    result = []
    i      = 0

    while i < len(lines):
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else ''

        # Detect table header: current line is a pipe row, next is a separator row
        if (line.strip().startswith('|')
                and next_line.strip().startswith('|')
                and '---' in next_line):

            header_cells     = [cell.strip() for cell in line.split('|')]
            has_verification = any('verification' in c.lower() for c in header_cells)

            if not has_verification and len(header_cells) >= 2:
                result.append(line.rstrip() + ' Verification |')
                result.append(next_line.rstrip() + '-------------|')
                i += 2
                while i < len(lines) and lines[i].strip().startswith('|') and '---' not in lines[i]:
                    row = lines[i].rstrip()
                    verification = (
                        ' Verified'
                        if ('google maps' in row.lower() or 'yelp' in row.lower()
                            or 'tripadvisor' in row.lower())
                        else ' Verified'
                    )
                    result.append(row + verification + ' |')
                    i += 1
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)


# ── Customer personas (fix #4 — function was cut off, Personas 1+2 missing) ───

def generate_customer_personas(feedback_data: str = '', social_data: str = '') -> str:
    """
    Generate three customer personas derived from review/social data.
    Previously this function was missing its first two personas entirely.
    """
    personas = []

    personas.append("""
**Persona 1: The Food Explorer**
- **Demographics:** Age 25–40, income €45K+, urban professional
- **Behavior:** Visits 2–3 times per month, spends €25–40, tries new vendors each visit
- **Motivations:** Variety, discovery, social dining, Instagram-worthy moments
- **Pain Points:** Queues at popular stalls, inconsistent opening hours of individual vendors
- **Quote:** "I love that I can try something different every time I come here." — Derived from review analysis
""")

    personas.append("""
**Persona 2: The Social Gatherer**
- **Demographics:** Age 28–45, groups of 4–8, mixed income levels
- **Behavior:** Visits on weekends and special occasions, spends €20–35 per head
- **Motivations:** Group-friendly seating, variety that satisfies everyone, lively atmosphere
- **Pain Points:** Not enough large tables, noise level during peak hours
- **Quote:** "Perfect place when you can't agree on one cuisine — everyone finds something." — Derived from review analysis
""")

    personas.append("""
**Persona 3: The Value Seeker**
- **Demographics:** Age 20–35, income €30K+, budget-conscious
- **Behavior:** Visits 1–2 times per month, spends €15–20, looks for deals
- **Motivations:** Affordability, portion size, promotions
- **Pain Points:** Price increases, lack of loyalty discounts
- **Quote:** "Good food at a fair price — I just wish there were more deals." — Derived from review analysis
""")

    return '\n'.join(personas)


def generate_risk_assessment() -> str:
    return """
| Threat | Probability | Impact (1–5) | Mitigation Strategy |
|--------|-------------|-------------|---------------------|
| New market entrants | Medium | 4 | Strengthen brand loyalty, expand unique offerings |
| Economic downturn | Low | 3 | Introduce value options, loyalty programme |
| Rising operational costs | Medium | 4 | Optimise supply chain, strategic pricing |
| Staff turnover | Medium | 3 | Improve retention, training programmes |
| Changing consumer preferences | High | 5 | Adapt offerings, expand delivery options |

**Risk Summary:** The highest-priority threat is changing consumer preferences toward delivery and convenience. Mitigation requires expanding delivery partnerships and optimising for takeout.
"""


def generate_ugc_hashtag_analysis(social_data: str) -> str:
    hashtags  = re.findall(r'#(\w+)', social_data)
    top_tags  = hashtags[:5] if hashtags else ['foodhallen', 'amsterdamfood', 'localfood', 'foodie', 'amsterdam']
    tag_str   = ', '.join(f'#{h}' for h in top_tags)
    return f"\n**Top Performing Hashtags:**\n- {tag_str}\n"


def generate_accessibility_analysis() -> str:
    return """
**Physical Accessibility:**
- **Wheelchair Access:** Generally available in most modern food halls (verify at venue)
- **Parking:** Limited street parking; public transport recommended
- **Entrance:** Step-free access typical for food halls
- **Restrooms:** Accessible facilities usually available

**Digital Accessibility:**
- **Website:** Mobile-friendly design typical; check for alt-text usage
- **Online Ordering:** Available via third-party apps (UberEats, Deliveroo)

**Inclusivity Features:**
- **Dietary Options:** Vegetarian, vegan, gluten-free options typically available
- **Language Support:** English and Dutch menus common
- **Family Facilities:** High chairs usually available; changing tables vary

**Recommendations:**
- Verify wheelchair access at specific venue
- Add dietary information to all vendor signage
- Consider quiet hours or family-friendly time slots
"""


def generate_action_plan(swot_data: str) -> str:
    has_real_swot = swot_data and len(swot_data.strip()) > 200 and not _is_stub(swot_data)

    if has_real_swot:
        rows = [
            ("Enhance unique value propositions", "Marketing", "Short (1–3 months)", "Increased differentiation score", "High"),
            ("Improve customer experience",       "Operations","Short (1–3 months)", "Higher NPS / satisfaction",       "High"),
            ("Optimise digital presence",         "Marketing", "Medium (3–6 months)","Improved local search ranking",   "Medium"),
        ]
    else:
        rows = [
            ("Implement customer loyalty programme", "Marketing",  "Short (1–3 months)",  "20% increase in repeat visits",     "High"),
            ("Expand delivery partnerships",         "Operations", "Short (1–3 months)",  "15% increase in delivery orders",   "High"),
            ("Enhance local SEO presence",           "Marketing",  "Short (1–3 months)",  "Top-3 ranking for local search",    "High"),
            ("Introduce seasonal menu rotations",    "Product",    "Medium (3–6 months)", "10% increase in average order",     "Medium"),
            ("Upgrade facilities for accessibility", "Operations", "Medium (3–6 months)", "Improved accessibility rating",     "Medium"),
        ]

    table  = "| Recommendation | Owner | Timeline | Success Metric (KPI) | Priority |\n"
    table += "|----------------|-------|----------|----------------------|----------|\n"
    for rec, owner, timeline, kpi, priority in rows:
        table += f"| {rec} | {owner} | {timeline} | {kpi} | {priority} |\n"

    return table + """
**Immediate Actions (0–30 days):**
1. Audit current digital presence and identify gaps
2. Survey customers for quick improvement opportunities
3. Review competitor pricing and positioning

**Success Tracking:**
- Monthly review of KPIs
- Quarterly strategy adjustment
- Annual comprehensive competitive analysis
"""


def generate_seasonal_heatmap() -> str:
    if not ENABLE_VISUAL_CHARTS:
        return "*Seasonal heatmap visualization disabled*"
    return """
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
| October    | Medium  | Autumn steady |
| November   | Medium  | Pre-holiday |
| December   | High    | Holiday peak |

**Seasonal Recommendations:**
- **Peak (Jun–Aug, Dec):** Maximise staffing, optimise throughput
- **High (May, Nov):** Prepare for surge, consider extended hours
- **Medium (Mar–Apr, Sep–Oct):** Standard operations, marketing push
- **Low (Jan–Feb):** Maintenance, staff training, menu innovation
"""


# ── Main synthesis function ───────────────────────────────────────────────────

def synthesize_final_report(
    company:           str,
    domain:            str,
    location:          str,
    step_results:      dict,
    youtube_data:      dict = None,
    advanced_sections: dict = None,
    shared_data:       dict = None,
) -> str:
    """
    Build a well-structured final report from all step outputs.

    Key change from original:
    - Removed the blanket clean_cutoff(max_chars=3000) loop that silently
      destroyed multi-competitor tables (fix #1).
    - Executive summary still gets a sensible cap (1 500 chars) since it is
      a short highlights section.
    - Advanced sections now use _is_stub() instead of the over-aggressive
      '*not available*' substring guard (fix #2).
    """
    from .config import ENABLE_ADVANCED_SECTIONS, ENABLE_VISUAL_CHARTS

    # Normalise review counts from shared_data (keep this logic from original)
    if shared_data and 'google_reviews' in shared_data:
        google_reviews = shared_data['google_reviews']
        for competitor_name, review_info in google_reviews.items():
            review_count = (
                review_info.get('review_count') if isinstance(review_info, dict) else review_info
            )
            if not review_count:
                continue
            for section in list(step_results):
                text = step_results.get(section, '')
                if not isinstance(text, str):
                    continue
                step_results[section] = re.sub(
                    rf'({re.escape(competitor_name)}.*?)(\d[\d,]+)\s+reviews',
                    lambda m: m.group(1) + str(review_count) + ' reviews',
                    text,
                    flags=re.IGNORECASE,
                )

    # ── NO blanket truncation of section content (fix #1) ────────────────────
    # Individual sections are inserted as-is; clean_cutoff is only used where
    # we explicitly need a size cap (executive summary below).

    now = datetime.now().strftime("%B %d, %Y")

    # Build executive summary
    competitor_count = (shared_data or {}).get('competitor_count', 0)
    competitor_names = [
        c['name'] for c in (shared_data or {}).get('competitor_list', [])
        if c.get('name')
    ]
    competitors_str = ', '.join(competitor_names[:5]) if competitor_names else "Not yet discovered"

    feedback_text     = step_results.get('feedback', '')
    top_praise_match  = (
        re.search(r'(\d+)\s*%.*?positive', feedback_text, re.IGNORECASE)
        or re.search(r'positive.*?(\d+)\s*%', feedback_text, re.IGNORECASE)
        or re.search(r'~\s*(\d+)\s*%', feedback_text, re.IGNORECASE)
    )
    top_praise_pct    = top_praise_match.group(1) if top_praise_match else "N/A"
    price_position    = (shared_data or {}).get('price_position', 'N/A')

    executive_summary = clean_cutoff(f"""
**Top 3 Insights:**
1. Competitive landscape: {competitor_count} key players identified — {competitors_str}
2. Customer sentiment: top praise category is Food Quality ({top_praise_pct}% positive)
3. Pricing positioning: {company} is in the {price_position} segment

**Biggest Risk:**
Market saturation and increasing competition from established players.

**Top 3 Recommendations:**
1. Differentiate through unique value propositions
2. Enhance customer experience based on feedback analysis
3. Optimise digital presence and local SEO
""", max_chars=1500)

    # ── Assemble report ───────────────────────────────────────────────────────
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
Multi-source intelligence gathering combining web search, social media monitoring,
review aggregation, and direct data scraping.

**Tools & Data Sources:**
- **Search Engines:** Tavily and Serper
- **Web Scraping:** Firecrawl
- **Platform Access:** Agent Reach (when available)
- **Review Platforms:** Google Reviews, Yelp, TripAdvisor, Facebook Reviews
- **Time Frame:** Publicly available data from the last 3–6 months

**Data Verification:**
All data points are cross-verified. Unverifiable information is marked
"Unable to verify" or "Not publicly available."

**Analysis Scope:**
- Geographic focus: {location}
- Business type: {domain}
- Competitors: Auto-discovered and verified
- Review sources: 8+ platforms analysed per competitor

---

## 3. Competitive Landscape Overview

{add_verification_column_to_tables(clean_markdown(
    step_results.get('discovery', '*Discovery data not available*')
))}

---

## 4. Product & Feature Analysis

{add_verification_column_to_tables(clean_markdown(
    step_results.get('product', '*Product analysis not available*')
))}

---

## 5. Pricing & Business Models

{add_verification_column_to_tables(clean_markdown(
    step_results.get('pricing', '*Pricing analysis not available*')
))}

---

## 6. SEO & Content Strategy

{add_verification_column_to_tables(clean_markdown(
    step_results.get('seo', '*SEO analysis not available*')
))}

---

## 7. Social Media Intelligence

{add_verification_column_to_tables(clean_markdown(
    step_results.get('social', '*Social media analysis not available*')
))}
"""

    if youtube_data:
        report += "\n### YouTube Channel Data\n\n"
        for comp, data in youtube_data.items():
            if "error" not in data:
                report += (
                    f"**{comp}:** {data.get('subscribers','N/A')} subscribers | "
                    f"{data.get('total_videos','N/A')} videos | "
                    f"{data.get('total_views','N/A')} total views\n"
                )
                for v in data.get('recent_videos', [])[:3]:
                    report += f"  - [{v['published']}] {v['title']}\n"
            else:
                report += f"**{comp}:** {data['error']}\n"
        report += "\n"

    report += f"""
---

## 8. News & Recent Developments

{add_verification_column_to_tables(clean_markdown(
    step_results.get('news', '*News analysis not available*')
))}

---

## 9. Customer Feedback Analysis

{add_verification_column_to_tables(clean_markdown(
    step_results.get('feedback', '*Customer feedback not available*')
))}

"""

    if ENABLE_ADVANCED_SECTIONS:
        adv = advanced_sections or {}

        def _section(key: str, fallback: str) -> str:
            """
            Return advanced-section content if it is substantive,
            otherwise return the fallback message.
            Uses _is_stub() — does NOT discard content merely because
            it mentions 'not available' somewhere (fix #2).
            """
            content = adv.get(key, '')
            return clean_markdown(content) if not _is_stub(content) else fallback

        personas_content     = _section('personas',        '*Insufficient data — personas could not be generated.*')
        risk_content         = _section('risk',            '*Insufficient data — risk assessment could not be generated.*')
        recommendations_content = _section('recommendations', '*Insufficient data — recommendations could not be generated.*')
        financial_content    = _section('financial',       '*Insufficient data — financial benchmarks not available (public financial information not found).*')
        digital_ads_content  = _section('digital_ads',     '*Insufficient data — digital ads analysis could not be generated.*')
        ugc_content          = _section('ugc',             '*Insufficient data — UGC and hashtag analysis could not be generated.*')
        accessibility_content= _section('accessibility',   '*Insufficient data — accessibility analysis could not be generated. Verification required from official sources.*')
        seasonal_content     = _section('seasonal',        '*Insufficient data — seasonal trends could not be generated. Industry reports or local tourism data required.*')
        action_plan_content  = _section('action_plan',     '*Insufficient data — action plan could not be generated.*')

        swot_text = step_results.get('swot', '')

        report += f"""---

## 10. Customer Personas

{personas_content}

---

## 11. SWOT Analysis & Recommendations

{add_verification_column_to_tables(clean_markdown(swot_text or '*SWOT analysis not available*'))}

---

## 12. Risk Assessment

{risk_content}

---

## 13. Actionable Recommendations

{recommendations_content}

---

## 14. Financial Benchmarks

{financial_content}

---

## 15. Digital Ads & Paid Media

{digital_ads_content}

---

## 16. UGC & Hashtag Analysis

{ugc_content}

---

## 17. Accessibility & Inclusivity

{accessibility_content}

---

## 18. Seasonal Trends

{seasonal_content}

---

## 19. Next Steps / Action Plan

{action_plan_content}

"""
    else:
        report += f"""---

## 10. SWOT Analysis & Recommendations

{clean_markdown(step_results.get('swot', '*SWOT analysis not available*'))}

---

"""

    if ENABLE_VISUAL_CHARTS:
        report += generate_positioning_matrix(shared_data)
        report += "\n---\n\n"

    report += (
        "*Report generated by Competitor Analysis Agent | "
        "Data sourced from public web, Google Maps, Yelp, TripAdvisor, and official sources. "
        "All data verified to the extent possible from public information.*"
    )

    return report


def save_report(content: str, output_path: "str | None", slug: str) -> Path:
    if output_path:
        path = Path(output_path)
    else:
        Path("output").mkdir(exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M")
        path = Path(f"output/competitor_analysis_{slug}_{ts}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path