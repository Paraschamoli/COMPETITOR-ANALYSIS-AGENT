#!/usr/bin/env python3
"""
Competitor Analysis Agent - Modular Version
Fixes: Social media scraping, report quality, Crawl4AI integration

Usage:
  python main_modular.py --company "Stripe" --domain "payment processing" --initial_competitors "Braintree, PayPal"
"""

import argparse
import re
from agent.config import (
    COORDINATOR_MODEL, AGENT_MODEL, CRAWL4AI_AVAILABLE,
    AGENT_REACH_AVAILABLE, YOUTUBE_AVAILABLE, ENABLE_ADVANCED_SECTIONS, GOOGLE_MAPS_SCRAPER_AVAILABLE
)
from agent.agents.competitor_discovery_agent import competitor_discovery_agent
from agent.agents.product_analysis_agent import product_analysis_agent
from agent.agents.pricing_business_agent import pricing_business_agent
from agent.agents.seo_content_agent import seo_content_agent
from agent.agents.social_media_agent import social_media_agent
from agent.agents.news_intelligence_agent import news_intelligence_agent
from agent.agents.customer_feedback_agent import customer_feedback_agent
from agent.agents.swot_synthesis_agent import swot_synthesis_agent
from agent.agents.advanced_sections_agent import advanced_sections_agent
from agent.tools import get_youtube_channel_stats
from agent.report_generator import synthesize_final_report, save_report, clean_cutoff

try:
    from agent.tools import TavilyTools, SerperTools

    SEARCH_TOOLS_AVAILABLE = True
except ImportError:
    TavilyTools = None  # type: ignore[misc, assignment]
    SerperTools = None  # type: ignore[misc, assignment]
    SEARCH_TOOLS_AVAILABLE = False

# Max chars passed into downstream agents (sentence-aware); full step_results stay intact for the report.
SWOT_CONTEXT_SECTION_MAX = 4000
ADVANCED_CONTEXT_SECTION_MAX = 2000

# Per-section overrides for SWOT context (issue #13: discovery and feedback need more chars)
SWOT_DISCOVERY_MAX = 6000
SWOT_PRODUCT_MAX   = 4000
SWOT_PRICING_MAX   = 3000
SWOT_FEEDBACK_MAX  = 4000
SWOT_NEWS_MAX      = 2000
SWOT_SOCIAL_MAX    = 2000

# Substrings (lowercase) matched against cleaned LLM headers → keys used by report_generator.py
SECTION_KEY_MAP = {
    "customer personas": "personas",
    "customer persona": "personas",
    "risk assessment": "risk",
    "actionable recommendations": "recommendations",
    "financial benchmarks": "financial",
    "digital ads": "digital_ads",
    "ugc": "ugc",
    "hashtag": "ugc",
    "accessibility": "accessibility",
    "seasonal": "seasonal",
    "next steps": "action_plan",
    "action plan": "action_plan",
}


def clean_advanced_section_header(header: str) -> str:
    """Strip markdown hashes, then leading digits, dots, and whitespace; lowercase."""
    s = re.sub(r"^#+\s*", "", header.strip())
    s = s.lstrip("0123456789. \t")
    return s.lower()


def map_advanced_header_to_canonical_key(header: str) -> str:
    """
    Map a section header to a short canonical key using SECTION_KEY_MAP substring rules.
    Unknown sections fall back to a snake_case slug of the cleaned header.
    """
    cleaned = clean_advanced_section_header(header)
    for phrase, canonical in SECTION_KEY_MAP.items():
        if phrase in cleaned:
            return canonical
    return re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_") or "misc"


def _hit_to_competitor_row(title: str, company: str) -> dict | None:
    name = (title or "").strip()
    if not name or name.strip().casefold() == company.strip().casefold():
        return None
    return {
        "name": name,
        "address": "",
        "rating": "",
        "review_count": "",
    }


def _extract_titles_from_result(result) -> list[str]:
    """Extract title strings from whatever agno search tools actually return.

    agno TavilyTools/SerperTools return a plain string (JSON-formatted or
    prose). We handle three cases:
      1. String  → regex-scan for "title": "..." JSON fields
      2. List    → iterate items; each item may be a dict or have a .title attr
      3. Object  → try .results / .organic then fall through to str()
    """
    titles: list[str] = []

    if isinstance(result, str):
        titles = re.findall(r'"title":\s*"([^"]+)"', result)

    elif isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                t = item.get("title") or item.get("name") or ""
            else:
                t = getattr(item, "title", "") or getattr(item, "name", "") or ""
            if t:
                titles.append(str(t))

    else:
        # Object with sub-collections (legacy path — kept as safe fallback)
        sub = getattr(result, "results", None) or getattr(result, "organic", None)
        if sub:
            return _extract_titles_from_result(sub)
        # Last resort: stringify and regex-scan
        titles = re.findall(r'"title":\s*"([^"]+)"', str(result))

    return titles


def _collect_competitors_from_search_query(query: str, company: str) -> list[dict]:
    """Run Tavily then Serper for one query; return competitor dict rows from result titles."""
    rows: list[dict] = []
    if not SEARCH_TOOLS_AVAILABLE or TavilyTools is None or SerperTools is None:
        return rows

    # ── Tavily ────────────────────────────────────────────────────────────────
    try:
        tavily_raw = TavilyTools().search(query)
        titles = _extract_titles_from_result(tavily_raw)[:5]
        for title in titles:
            row = _hit_to_competitor_row(title, company)
            if row:
                rows.append(row)
        if rows:
            print(f"     Tavily extracted {len(rows)} names for: {query}")
            return rows
    except Exception as e:
        print(f"     ⚠️  Tavily failed ({e}); trying Serper...")

    # ── Serper (fallback) ─────────────────────────────────────────────────────
    try:
        serper_raw = SerperTools().search(query)
        titles = _extract_titles_from_result(serper_raw)[:5]
        for title in titles:
            row = _hit_to_competitor_row(title, company)
            if row:
                rows.append(row)
        if rows:
            print(f"     Serper extracted {len(rows)} names for: {query}")
    except Exception as e:
        print(f"     ⚠️  Serper failed ({e})")

    return rows


def parse_args():
    parser = argparse.ArgumentParser(description="Local Business Competitor Analysis Agent")
    parser.add_argument("--company", required=True, help='Target business: "Foodhallen"')
    parser.add_argument("--domain", required=True, help='Business type: "cafe", "restaurant", "bar", "shop", "service"')
    parser.add_argument("--location", required=True, help='Location: "Amsterdam", "New York", "London"')
    parser.add_argument("--initial_competitors", default="Auto-discovered",
                        help='Starting competitors: " competitor1, competitor2"')
    parser.add_argument("--output", default=None, help="Output file path")
    parser.add_argument("--skip-youtube", action="store_true", help="Skip YouTube API calls")
    return parser.parse_args()


def banner(args):
    w = 80
    print("\n" + "═" * w)
    print("  🔍  LOCAL BUSINESS COMPETITOR ANALYSIS AGENT")
    print("═" * w)
    print(f"  Business       : {args.company}")
    print(f"  Type           : {args.domain}")
    print(f"  Location       : {args.location}")
    print(f"  Competitors    : {args.initial_competitors}")
    print(f"  Models         : {COORDINATOR_MODEL} / {AGENT_MODEL}")
    print(f"  Crawl4AI       : {'✅ Available' if CRAWL4AI_AVAILABLE else '❌ Not installed'}")
    print(f"  Agent Reach    : {'✅ Available' if AGENT_REACH_AVAILABLE else '❌ Not installed'}")
    print(f"  Google Maps Scraper : {'✅ Available' if GOOGLE_MAPS_SCRAPER_AVAILABLE else '❌ Not available (Docker required)'}")
    print(f"  Advanced Sects : {'✅ Enabled' if ENABLE_ADVANCED_SECTIONS else '❌ Disabled (set ENABLE_ADVANCED_SECTIONS=true)'}")
    print("═" * w)
    
    # Local business capabilities
    print("  📍 Local Focus: Google Maps, local reviews, community engagement")
    print("  🏪 Business Types: Cafes, restaurants, bars, shops, services")
    print("  📱 Platforms: Google, Yelp, TripAdvisor, Instagram, Facebook")
    
    if AGENT_REACH_AVAILABLE:
        print("  📊 Enhanced Platform Access: Social media insights")
    else:
        print("  ⚠️  To enable enhanced platform access:")
        print("       Install: https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md")
    print("\n")


def run_step(
    step_name: str,
    agent,
    prompt: str,
    *,
    company: str,
    domain: str,
    location: str,
) -> str:
    """Run a single agent step with error handling."""
    print(f"  ⏳ {step_name}...")
    try:
        result = agent.run(
            prompt,
            session_state={"company": company, "domain": domain, "location": location},
        )
        content = ""
        if hasattr(result, "content"):
            content = result.content
        elif isinstance(result, str):
            content = result
        else:
            content = str(result)
        print(f"  ✅ {step_name} complete ({len(content)} chars)")
        return content
    except Exception as e:
        print(f"  ❌ {step_name} failed")
        return f"Error: {step_name} failed – data not available."


def main():
    args = parse_args()
    banner(args)
    
    company = args.company
    domain = args.domain
    location = args.location
    competitors_seed = args.initial_competitors
    
    context = f"Business: {company} | Type: {domain} | Location: {location} | Known competitors: {competitors_seed}"
    step_results = {}
    youtube_data = {}
    
    # Shared data for cross-agent communication
    shared_data = {
        'competitor_count': 0,
        'competitor_list': [],
        'google_reviews': {}
    }

    # ── Step 1: Competitor Discovery ──────────────────────────────────────────
    print("\n📋 Step 1/7: Local Competitor Discovery")
    step_results["discovery"] = run_step(
        "Local Competitor Discovery",
        competitor_discovery_agent(),
        f"{context}\n\nDiscover and profile all local competitors for {company} in the {domain} category in {location}."
        f" Start with these known competitors: {competitors_seed}, then find more local businesses.",
        company=company,
        domain=domain,
        location=location,
    )

    # ── FIX #14: Reliable competitor counting ────────────────────────────────
    # Primary: count actual data rows in the discovery markdown table
    discovery_lines = step_results['discovery'].split('\n')
    table_lines = [
        l for l in discovery_lines
        if l.strip().startswith('|') and '---' not in l and l.strip() != '|'
    ]
    # Subtract 1 for the header row
    row_count = max(0, len(table_lines) - 1)

    # Parse competitor structs from those same table rows (used by downstream steps)
    competitors = []
    for row in table_lines[1:]:  # skip header
        if row.strip():
            columns = [col.strip() for col in row.split('|')]
            if len(columns) >= 5:
                competitor = {
                    'name': columns[1] if len(columns) > 1 else '',
                    'address': columns[2] if len(columns) > 2 else '',
                    'rating': columns[3] if len(columns) > 3 else '',
                    'review_count': columns[4] if len(columns) > 4 else ''
                }
                if competitor['name'] and competitor['name'] != company:
                    competitors.append(competitor)

    shared_data['competitor_list'] = competitors

    # Secondary: count from parsed list (catches rows that may have been filtered above)
    list_count = len([c for c in competitors if c.get('name') and c['name'] != company])

    # Tertiary fallback: original regex (only when both primary counts are 0)
    regex_count = 0
    if row_count == 0 and list_count == 0:
        count_match = re.search(r"(\d+)\s*(?:competitors|key players)", step_results['discovery'], re.IGNORECASE)
        if count_match:
            regex_count = int(count_match.group(1))

    # Use the most reliable signal available
    if row_count > 0 or list_count > 0:
        shared_data['competitor_count'] = max(row_count, list_count)
        print(f"  📊 Competitor count via: {'table rows' if row_count >= list_count else 'list parsing'}")
    else:
        shared_data['competitor_count'] = regex_count
        print(f"  📊 Competitor count via: regex fallback")

    print(f"  📊 Discovered {shared_data['competitor_count']} competitors (excluding {company})")

    # Check if discovery failed or has insufficient competitors, then use deterministic fallback
    if "Error:" in step_results["discovery"] or shared_data["competitor_count"] < 6:
        print("  🔄 Discovery failed or insufficient competitors. Running deterministic fallback...")

        if not SEARCH_TOOLS_AVAILABLE:
            print("  ⚠️  Search tools (Tavily/Serper) not available — cannot run web fallback.")
            shared_data["competitor_list"] = competitors
            shared_data["competitor_count"] = len(competitors)
            if len(competitors) < 6:
                print(
                    f"  ⚠️  Only {len(competitors)} real competitors found. Report will cover available competitors only."
                )
        else:
            fallback_competitors: list[dict] = [dict(c) for c in competitors]
            search_queries = [
                f"{domain} near {location}",
                f"best {domain} in {location}",
                f"top {domain} {location}",
            ]
            for query in search_queries:
                print(f"  🔍 Searching: {query}")
                try:
                    fallback_competitors.extend(_collect_competitors_from_search_query(query, company))
                except Exception:
                    print(f"  ⚠️  Search query failed: {query}")
                    continue

            unique_competitors: list[dict] = []
            seen_names: set[str] = set()
            for comp in fallback_competitors:
                n = comp.get("name", "").strip()
                if n and n not in seen_names:
                    seen_names.add(n)
                    unique_competitors.append(comp)

            if len(unique_competitors) < 6:
                second_pass_queries = [
                    f"'{domain}' venue {location} site:google.com/maps",
                    f"top rated {domain} {location} tripadvisor",
                    f"{domain} {location} recommended",
                ]
                for query in second_pass_queries:
                    print(f"  🔍 Second-pass search: {query}")
                    try:
                        for row in _collect_competitors_from_search_query(query, company):
                            n = row.get("name", "").strip()
                            if n and n not in seen_names:
                                seen_names.add(n)
                                unique_competitors.append(row)
                    except Exception:
                        print(f"  ⚠️  Second-pass query failed: {query}")
                        continue

            if len(unique_competitors) < 6:
                print(
                    f"  ⚠️  Only {len(unique_competitors)} real competitors found. Report will cover available competitors only."
                )

            shared_data["competitor_list"] = unique_competitors
            shared_data["competitor_count"] = len(unique_competitors)
            print(f"  📊 Fallback enriched list: {shared_data['competitor_count']} competitors (real names only)")

    # Build structured competitor list for explicit injection into prompts
    competitor_names = [comp["name"] for comp in shared_data["competitor_list"] if comp.get("name")]
    competitor_list_str = "\n".join(f"- {name}" for name in competitor_names)
    if competitor_names:
        competitor_prompt_addition = (
            f"\n\nDiscovered competitors (analyze every business listed — there are {len(competitor_names)}):\n"
            f"{competitor_list_str}"
        )
    else:
        competitor_prompt_addition = "\n\nNo structured competitor list was extracted; infer competitors from the context and search results."

    # ── Step 2: Product & Service Analysis ──────────────────────────────────────
    print("\n🔬 Step 2/7: Product & Service Analysis")
    step_results["product"] = run_step(
        "Product & Service Analysis",
        product_analysis_agent(),
        f"{context}{competitor_prompt_addition}\n\n"
        f"Now do deep product/service analysis for each competitor vs {company} in {location}.",
        company=company,
        domain=domain,
        location=location,
    )

    # ── Step 3: Pricing & Business Model ──────────────────────────────────────
    print("\n💰 Step 3/7: Pricing & Business Model Analysis")
    step_results["pricing"] = run_step(
        "Pricing Analysis",
        pricing_business_agent(),
        f"{context}{competitor_prompt_addition}\n\n"
        f"Analyze pricing and business model for {company} and all discovered local competitors in {location}.",
        company=company,
        domain=domain,
        location=location,
    )
    
    # Extract price position from pricing output
    pricing_text = step_results["pricing"]
    price_position = "Data not available"
    if '€€€' in pricing_text:
        price_position = "Premium"
    elif '€€' in pricing_text:
        price_position = "Mid-range"
    elif '€' in pricing_text:
        price_position = "Budget"
    elif 'premium' in pricing_text.lower():
        price_position = "Premium"
    elif 'mid-range' in pricing_text.lower() or 'mid range' in pricing_text.lower():
        price_position = "Mid-range"
    elif 'budget' in pricing_text.lower() or 'low-cost' in pricing_text.lower():
        price_position = "Budget"
    shared_data['price_position'] = price_position
    print(f"  💰 Price position: {price_position}")

    # ── Step 4: Local SEO & Content ────────────────────────────────────────────────
    print("\n🔍 Step 4/7: Local SEO & Content Strategy")
    step_results["seo"] = run_step(
        "Local SEO Analysis",
        seo_content_agent(),
        f"{context}{competitor_prompt_addition}\n\n"
        f"Analyze local SEO presence and content strategy for {company} and all competitors in {location}.",
        company=company,
        domain=domain,
        location=location,
    )

    # ── Step 5: Social Media Intelligence ────────────────────────────────────────
    print("\n📱 Step 5/7: Social Media Intelligence")
    step_results["social"] = run_step(
        "Social Media Analysis",
        social_media_agent(),
        f"{context}{competitor_prompt_addition}\n\n"
        f"Analyze social media presence for {company} and all local competitors in {location}."
        f" Focus on local platforms and community engagement.",
        company=company,
        domain=domain,
        location=location,
    )
    
    # YouTube API supplement (if configured)
    if YOUTUBE_AVAILABLE and not args.skip_youtube:
        print("  🎬 Fetching YouTube stats via API...")
        key_competitors = competitors_seed.split(",") + [company]
        for comp in key_competitors[:5]:
            comp = comp.strip()
            if comp:
                youtube_data[comp] = get_youtube_channel_stats(comp)
                print(f"     YouTube data for {comp}: {youtube_data[comp].get('subscribers', 'N/A')} subscribers")

    # ── Step 6: Local News & Intelligence ────────────────────────────────────────
    print("\n📰 Step 6/7: Local News & Market Intelligence")
    step_results["news"] = run_step(
        "Local News Analysis",
        news_intelligence_agent(),
        f"{context}{competitor_prompt_addition}\n\n"
        f"Find recent local news, events, and developments for {company} and competitors in {location}."
        f" Focus on last 3-6 months of local business activity.",
        company=company,
        domain=domain,
        location=location,
    )

    # ── Step 7: Customer Feedback ─────────────────────────────────────────────
    print("\n💬 Step 7/7: Customer Feedback Analysis")
    step_results["feedback"] = run_step(
        "Customer Feedback",
        customer_feedback_agent(),
        f"{context}{competitor_prompt_addition}\n\n"
        f"Mine customer reviews from Google, Yelp, TripAdvisor for {company} and all local competitors in {location}.",
        company=company,
        domain=domain,
        location=location,
    )
    
    # Extract Google review counts and ratings from feedback output
    import json
    feedback_text = step_results['feedback']
    
    if GOOGLE_MAPS_SCRAPER_AVAILABLE:
        json_pattern = r'\{[^{}]*"review_count"[^{}]*\}'
        for match in re.finditer(json_pattern, feedback_text):
            try:
                data = json.loads(match.group())
                if 'title' in data and 'review_count' in data:
                    competitor_name = data['title']
                    review_count = data['review_count']
                    rating = data.get('rating', data.get('avgRating', None))
                    shared_data['google_reviews'][competitor_name] = {'rating': rating, 'count': review_count}
            except json.JSONDecodeError:
                continue
    
    rating_count_pattern = r'([A-Za-z\s]+?)[\s:]+(\d+\.?\d*)[/\s]*(?:5|stars)[\s\(\)]+(\d+)\s+reviews'
    for match in re.finditer(rating_count_pattern, feedback_text, re.IGNORECASE):
        competitor_name = match.group(1).strip()
        rating = float(match.group(2))
        review_count = int(match.group(3))
        if competitor_name not in shared_data['google_reviews']:
            shared_data['google_reviews'][competitor_name] = {'rating': rating, 'count': review_count}
    
    for competitor in shared_data['competitor_list']:
        competitor_name = competitor['name']
        if competitor_name not in shared_data['google_reviews']:
            rating_match = re.search(rf'{re.escape(competitor_name)}[^\n]*?(\d+\.?\d*)[/\s]*(?:5|stars)', feedback_text, re.IGNORECASE)
            count_match_fb = re.search(rf'{re.escape(competitor_name)}[^\n]*?(\d+)\s+reviews', feedback_text, re.IGNORECASE)
            rating = float(rating_match.group(1)) if rating_match else None
            count = int(count_match_fb.group(1)) if count_match_fb else None
            if rating or count:
                shared_data['google_reviews'][competitor_name] = {'rating': rating, 'count': count}
    
    print(f"  📊 Extracted Google review data for {len(shared_data['google_reviews'])} competitors")

    # ── SWOT Synthesis ────────────────────────────────────────────────
    print("\n🎯 Bonus: SWOT Analysis & Strategic Recommendations")
    
    competitor_count = shared_data.get('competitor_count')
    competitor_list = shared_data.get('competitor_list')

    # Guard: skip only when there is truly no competitor data
    if not competitor_count or not competitor_list:
        step_results["swot"] = "Insufficient data for SWOT analysis – competitor discovery failed."
        print("  ⚠️  SWOT analysis skipped due to insufficient competitor data")
    else:
        # ── FIX #13: inject competitor names list + larger context slices ────
        competitor_list_for_swot = '\n'.join(
            f"- {c['name']} (rating: {c.get('rating', 'N/A')})"
            for c in shared_data['competitor_list']
            if c.get('name')
        )

        swot_context = f"""
Business: {company} | Type: {domain} | Location: {location}
Competitor Count: {shared_data['competitor_count']}

Competitors to include in SWOT (you MUST generate a SWOT table for EACH one):
{competitor_list_for_swot}

Key Local Research Findings:
- Local Competitor Discovery: {clean_cutoff(step_results['discovery'], max_chars=SWOT_DISCOVERY_MAX)}
- Product & Service Analysis: {clean_cutoff(step_results['product'], max_chars=SWOT_PRODUCT_MAX)}
- Pricing & Business Model: {clean_cutoff(step_results['pricing'], max_chars=SWOT_PRICING_MAX)}
- Customer Feedback: {clean_cutoff(step_results['feedback'], max_chars=SWOT_FEEDBACK_MAX)}
- Local News & Events: {clean_cutoff(step_results['news'], max_chars=SWOT_NEWS_MAX)}
- Social Media: {clean_cutoff(step_results['social'], max_chars=SWOT_SOCIAL_MAX)}
"""
        step_results["swot"] = run_step(
            "SWOT Analysis",
            swot_synthesis_agent(),
            swot_context,
            company=company,
            domain=domain,
            location=location,
        )

    # ── Advanced Sections (if enabled) ────────────────────────────────────────
    advanced_sections = {}
    if ENABLE_ADVANCED_SECTIONS:
        print("\n🚀 Advanced: Strategic Analysis & Recommendations")
        advanced_context = f"""
Business: {company} | Type: {domain} | Location: {location}

Complete Research Summary:
- Discovery: {clean_cutoff(step_results['discovery'], max_chars=ADVANCED_CONTEXT_SECTION_MAX)}
- Product: {clean_cutoff(step_results['product'], max_chars=ADVANCED_CONTEXT_SECTION_MAX)}
- Pricing: {clean_cutoff(step_results['pricing'], max_chars=ADVANCED_CONTEXT_SECTION_MAX)}
- SEO: {clean_cutoff(step_results['seo'], max_chars=ADVANCED_CONTEXT_SECTION_MAX)}
- Social: {clean_cutoff(step_results['social'], max_chars=ADVANCED_CONTEXT_SECTION_MAX)}
- News: {clean_cutoff(step_results['news'], max_chars=ADVANCED_CONTEXT_SECTION_MAX)}
- Feedback: {clean_cutoff(step_results['feedback'], max_chars=ADVANCED_CONTEXT_SECTION_MAX)}
- SWOT: {clean_cutoff(step_results['swot'], max_chars=ADVANCED_CONTEXT_SECTION_MAX)}
"""
        advanced_result = run_step(
            "Advanced Strategic Analysis",
            advanced_sections_agent(),
            advanced_context,
            company=company,
            domain=domain,
            location=location,
        )
        sections = {}
        current_section = None
        current_content = []
        for line in advanced_result.split('\n'):
            if line.startswith('###') or line.startswith('##'):
                if current_section:
                    canonical_key = map_advanced_header_to_canonical_key(current_section)
                    sections[canonical_key] = '\n'.join(current_content)
                current_section = line.strip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        if current_section:
            canonical_key = map_advanced_header_to_canonical_key(current_section)
            sections[canonical_key] = '\n'.join(current_content)
        advanced_sections = sections
        print(f"  Advanced section keys: {sorted(advanced_sections.keys())}")

    # ── Build Final Report ────────────────────────────────────────────────────
    print("\n📄 Building final report...")
    final_report = synthesize_final_report(
        company=company,
        domain=domain,
        location=location,
        step_results=step_results,
        youtube_data=youtube_data if youtube_data else None,
        advanced_sections=advanced_sections if advanced_sections else None,
        shared_data=shared_data
    )

    slug = f"{company}_{domain}_{location}".replace(" ", "_").lower()[:50]
    path = save_report(final_report, args.output, slug)

    print("\n" + "=" * 80)
    print(f"  ✅ Analysis Complete!")
    print(f"  📁 Report saved → {path}")
    print(f"  📊 Total: {len(final_report):,} chars | {len(final_report.split(chr(10)))} lines")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()