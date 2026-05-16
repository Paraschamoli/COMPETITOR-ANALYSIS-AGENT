#!/usr/bin/env python3
"""
Competitor Analysis Agent - Modular Version
Fixes: Social media scraping, report quality, Crawl4AI integration

Usage:
  python main_modular.py --company "Stripe" --domain "payment processing" --initial_competitors "Braintree, PayPal"
"""

import argparse
import logging
import re
import time
from agent.config import (
    COORDINATOR_MODEL, AGENT_MODEL, CRAWL4AI_AVAILABLE,
    AGENT_REACH_AVAILABLE, YOUTUBE_AVAILABLE, ENABLE_ADVANCED_SECTIONS, GOOGLE_MAPS_SCRAPER_AVAILABLE
)
from agent.models import CompetitorProfile
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
# Increased limits to prevent data loss from excessive truncation
SWOT_CONTEXT_SECTION_MAX = 20000
ADVANCED_CONTEXT_SECTION_MAX = 20000

# Per-section overrides for SWOT context - all increased significantly
SWOT_DISCOVERY_MAX = 15000
SWOT_PRODUCT_MAX   = 15000
SWOT_PRICING_MAX   = 15000
SWOT_FEEDBACK_MAX  = 15000
SWOT_NEWS_MAX      = 15000
SWOT_SOCIAL_MAX    = 15000

# Per-section overrides for advanced context (Sections 12–19 need more context)
ADVANCED_DISCOVERY_MAX = 20000
ADVANCED_FEEDBACK_MAX   = 20000

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


# Aggregator domains/names to reject in titles
AGGREGATOR_REJECT_PATTERNS = [
    "reddit", "tripadvisor", "yelp", "yelp.com", "quora",
    "2foodtrippers", "eater", "timeout", "thrillist",
    "infatuation", "lonelyplanet", "booking.com",
    "traveling outside the box", "askberliners", "pourover",
]

# Superlative / article-pattern phrases that signal a non-business title
TITLE_REJECT_PATTERNS = [
    r"^best\s", r"^top\s", r"^great\s", r"^\d+\s",
    r"^guide to\s", r"^where to\s",
    r"\s:\s*r/", r"\sreddit", r"\s–\s+\w+\s+\w+\s+\w+",  # : r/, reddit, " – word word word"
]


def validate_business_name(name: str, location: str) -> bool:
    """
    Follow-up search for "{name} {location} address opening hours".
    Returns True only if the top result contains a street address pattern
    or the words 'hours'/'open'/'closed'.
    On exception: pass-through (default True) so network errors don't block all competitors.
    """
    if not SEARCH_TOOLS_AVAILABLE or TavilyTools is None:
        return True

    from agno.agent import Agent
    from agent.models import agent_model

    followup_query = f"{name} {location} address opening hours"
    try:
        agent = Agent(
            tools=[TavilyTools()],
            model=agent_model(),
            instructions=["Search and return only the top result snippet."],
        )
        result = agent.run(f"Search for: {followup_query}")
        snippet = str(getattr(result, "content", "") or result).lower()

        # Street address pattern: digits followed by a street word
        address_pattern = re.search(r"\d+\s+\w+\s+(street|st\.|avenue|ave\.|road|rd\.|boulevard|blvd\.|drive|dr\.|lane|ln\.|way|place|pl\.|court)", snippet)
        if address_pattern:
            return True

        # Hours-related keywords
        if any(kw in snippet for kw in ["hours", "open", "closed"]):
            return True

        return False
    except Exception:
        return True  # pass-through on error


def _hit_to_competitor_row(title: str, company: str) -> dict | None:
    name = (title or "").strip()
    name_lower = name.lower()

    if not name or name.casefold() == company.strip().casefold():
        return None

    # Reject: title too long (real business names are short)
    if len(name) > 60:
        print(f"  [!] Rejected non-business title: {name[:60]}")
        return None

    # Reject: contains " - " followed by an aggregator name
    if " - " in name:
        after_dash = name.split(" - ", 1)[1].lower()
        for agg in AGGREGATOR_REJECT_PATTERNS:
            if agg.lower() in after_dash:
                print(f"  [!] Rejected non-business title: {name[:60]}")
                return None

    # Reject: matches any superlative / article pattern
    for pattern in TITLE_REJECT_PATTERNS:
        if re.search(pattern, name_lower):
            print(f"  [!] Rejected non-business title: {name[:60]}")
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


def _collect_competitors_from_search_query(query: str, company: str, location: str = "") -> list[dict]:
    """Run Tavily then Serper for one query; return competitor dict rows from result titles."""
    rows: list[dict] = []
    if not SEARCH_TOOLS_AVAILABLE or TavilyTools is None or SerperTools is None:
        return rows

    from agno.agent import Agent
    from agent.models import agent_model

    # ── Tavily ────────────────────────────────────────────────────────────────
    try:
        tavily_agent = Agent(
            tools=[TavilyTools()],
            model=agent_model(),
            instructions=[f"Search for: {query}. Return only business names, one per line."],
        )
        tavily_result = tavily_agent.run(f"Search for: {query}")
        titles = _extract_titles_from_result(tavily_result)[:5]
        for title in titles:
            row = _hit_to_competitor_row(title, company)
            if row:
                # Follow-up validation
                if location and not validate_business_name(row["name"], location):
                    print(f"  [!] Rejected non-business name after follow-up: {row['name'][:60]}")
                    continue
                rows.append(row)
        if len(rows) < 2:
            rows.clear()
        elif rows:
            print(f"     Tavily extracted {len(rows)} names for: {query}")
            return rows
    except Exception as e:
        print(f"     [!] Tavily failed ({e}); trying Serper...")

    # ── Serper (fallback) ─────────────────────────────────────────────────────
    try:
        serper_agent = Agent(
            tools=[SerperTools()],
            model=agent_model(),
            instructions=[f"Search for: {query}. Return only business names, one per line."],
        )
        serper_result = serper_agent.run(f"Search for: {query}")
        titles = _extract_titles_from_result(serper_result)[:5]
        for title in titles:
            row = _hit_to_competitor_row(title, company)
            if row:
                # Follow-up validation
                if location and not validate_business_name(row["name"], location):
                    print(f"  [!] Rejected non-business name after follow-up: {row['name'][:60]}")
                    continue
                rows.append(row)
        if len(rows) < 2:
            rows.clear()
        elif rows:
            print(f"     Serper extracted {len(rows)} names for: {query}")
    except Exception as e:
        print(f"     [!] Serper failed ({e})")

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
    print("\n" + "=" * w)
    print("  LOCAL BUSINESS COMPETITOR ANALYSIS AGENT")
    print("=" * w)
    print(f"  Business       : {args.company}")
    print(f"  Type           : {args.domain}")
    print(f"  Location       : {args.location}")
    print(f"  Competitors    : {args.initial_competitors}")
    print(f"  Models         : {COORDINATOR_MODEL} / {AGENT_MODEL}")
    print(f"  Crawl4AI       : {'[+] Available' if CRAWL4AI_AVAILABLE else '[-] Not installed'}")
    print(f"  Agent Reach    : {'[+] Available' if AGENT_REACH_AVAILABLE else '[-] Not installed'}")
    print(f"  Google Maps Scraper : {'[+] Available' if GOOGLE_MAPS_SCRAPER_AVAILABLE else '[-] Not available (Docker required)'}")
    print(f"  Advanced Sects : {'[+] Enabled' if ENABLE_ADVANCED_SECTIONS else '[-] Disabled (set ENABLE_ADVANCED_SECTIONS=true)'}")
    print("=" * w)
    
    # Local business capabilities
    print(f"  Target: {args.domain.title()} in {args.location}")
    print(f"  Business: {args.company}")
    print("  Platforms: Google, Yelp, TripAdvisor, Instagram, Facebook")

    if AGENT_REACH_AVAILABLE:
        print("  Social media insights via Agent Reach")
    else:
        print("  [!] Enhanced platform access not enabled")
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
    min_content_length: int = 100,  # Minimum chars to consider successful
) -> str | None:
    """Run a single agent step with error handling and retry logic.

    Prompt is formatted with company/domain/location; agent instructions are
    handled by agno as the system prompt — not injected into user content.
    Returns None on final failure so callers can detect the failure state.

    Args:
        min_content_length: Minimum characters required to consider the step successful.
                           If agent returns less, it will be retried.
    """
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds, doubled on each retry

    print(f"  Running: {step_name}...")
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Use safe string replacement that handles curly braces in content
            # This avoids KeyError from .format() when content contains { or }
            formatted_prompt = (
                prompt.replace('{company}', company)
                .replace('{domain}', domain)
                .replace('{location}', location)
            )

            result = agent.run(
                formatted_prompt,
                session_state={"company": company, "domain": domain, "location": location},
            )
            content = ""
            if hasattr(result, "content") and result.content is not None:
                content = result.content
            elif isinstance(result, str):
                content = result
            elif result is not None:
                content = str(result)
            else:
                content = ""

            # Check if content is too short - retry with warning
            content_len = len(content.strip()) if content else 0
            if content_len < min_content_length:
                if attempt < MAX_RETRIES:
                    wait = RETRY_DELAY * attempt
                    print(f"  [!] {step_name} returned only {content_len} chars (need {min_content_length})")
                    print(f"  [!] Retrying {step_name} in {wait}s (attempt {attempt+1}/{MAX_RETRIES})...")
                    time.sleep(wait)
                    continue
                else:
                    print(f"  [!] {step_name} completed but with minimal content ({content_len} chars)")

            print(f"  [+] {step_name} complete ({len(content)} chars)")
            return content if content else None

        except Exception as e:
            last_error = e
            logging.exception(f"{step_name} attempt {attempt}/{MAX_RETRIES} failed")
            if attempt < MAX_RETRIES:
                wait = RETRY_DELAY * attempt
                print(f"  [!] Retrying {step_name} in {wait}s (attempt {attempt+1}/{MAX_RETRIES})...")
                time.sleep(wait)

    print(f"  [-] {step_name} failed after {MAX_RETRIES} attempts: {last_error}")
    return None


def main():
    args = parse_args()
    banner(args)
    
    company = args.company
    domain = args.domain
    location = args.location
    competitors_seed = args.initial_competitors
    
    context = f"Business: {company} | Type: {domain} | Location: {location} | Known competitors: {competitors_seed}"
    target_analysis_instruction = (
        f"\n\nANALYSIS ORDER — MANDATORY:\n"
        f"1. First, fully analyze the TARGET business: {company}\n"
        f"   - Give {company} its own complete section with ALL fields filled\n"
        f"   - This is the business we are advising; it must appear in every table\n"
        f"2. Then analyze each competitor listed below\n"
        f"3. In all comparison tables, always include {company} as the first row\n"
    )
    step_results = {}
    youtube_data = {}
    shared_data = {
        "company": company,
        "competitor_count": 0,
        "competitor_list": [],
        "canonical_reviews": {},
        "google_reviews": {},
        "per_competitor_prices": {},
    }

    # ── Step 1: Competitor Discovery ──────────────────────────────────────────
    print("\nStep 1/7: Local Competitor Discovery")
    _result = run_step(
        "Local Competitor Discovery",
        competitor_discovery_agent(),
        f"{context}\n\nThe target business is {company}. Include it in the comparison matrix as the baseline row with label '[TARGET]' before listing competitors."
        f"\n\nDiscover and profile all local competitors for {company} in the {domain} category in {location}."
        f" Start with these known competitors: {competitors_seed}, then find more local businesses.",
        company=company,
        domain=domain,
        location=location,
    )
    if _result is None:
        step_results["discovery"] = ""
        print("  [!] Discovery skipped -- using empty placeholder")
    else:
        step_results["discovery"] = _result

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
                # Parse rating as float if possible
                rating_val = None
                try:
                    rating_str = columns[3] if len(columns) > 3 else ''
                    if rating_str:
                        rating_val = float(rating_str.split('/')[0])
                except (ValueError, IndexError):
                    pass

                # Parse review count as int if possible
                review_count_val = None
                try:
                    review_str = columns[4] if len(columns) > 4 else ''
                    if review_str:
                        review_count_val = int(review_str.replace(',', ''))
                except ValueError:
                    pass

                try:
                    # Determine which column has the actual competitor name
                    # Skip if the first column looks like a row number (pure digits)
                    raw_name = columns[1] if len(columns) > 1 else ''
                    if raw_name.strip().isdigit():
                        # Try next column - table might have # column first
                        raw_name = columns[2] if len(columns) > 2 else ''
                    # Also skip if name is empty or just whitespace
                    if not raw_name.strip() or raw_name.strip() == company:
                        continue

                    profile = CompetitorProfile(
                        name=raw_name,
                        address=columns[2] if len(columns) > 2 else '',
                        rating=rating_val,
                        review_count=review_count_val
                    )
                    if profile.name and profile.name != company:
                        competitors.append(profile.model_dump())
                except Exception as e:
                    logger.warning(f"Skipping invalid competitor row: {e}")

    shared_data['competitor_list'] = competitors

    # ── Canonical review data from discovery ───────────────────────────────────
    # Populate canonical_reviews with verified discovery data before downstream agents run
    for comp in competitors:
        name = comp.get('name', '')
        rating_str = comp.get('rating', '')
        review_str = comp.get('review_count', '')
        if name and (rating_str or review_str):
            shared_data['canonical_reviews'][name] = {
                'rating': rating_str,
                'count': review_str,
                'source': 'discovery'
            }

    # Build canonical_data_injection for downstream prompts
    lines = ["CANONICAL DATA — USE THESE EXACT VALUES, DO NOT SEARCH FOR NEW ONES:"]
    for name, data in shared_data['canonical_reviews'].items():
        lines.append(f"  - {name}: Rating {data['rating']}, Reviews {data['count']}")
    canonical_data_injection = "\n".join(lines)

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
        print(f"  [!] Competitor count via: {'table rows' if row_count >= list_count else 'list parsing'}")
    else:
        shared_data['competitor_count'] = regex_count
        print(f"  [!] Competitor count via: regex fallback")

    print(f"  Discovered {shared_data['competitor_count']} competitors (excluding {company})")

    # Check if discovery failed or has insufficient competitors, then use deterministic fallback
    if "Error:" in step_results["discovery"] or shared_data["competitor_count"] < 6:
        print("  [!] Discovery failed or insufficient competitors. Running deterministic fallback...")

        if not SEARCH_TOOLS_AVAILABLE:
            print("  Search tools (Tavily/Serper) not available — cannot run web fallback.")
            shared_data["competitor_list"] = competitors
            shared_data["competitor_count"] = len(competitors)
            if len(competitors) < 6:
                print(
                    f"  [!] Only {len(competitors)} real competitors found. Report will cover available competitors only."
                )
        else:
            fallback_competitors: list[dict] = [dict(c) for c in competitors]
            search_queries = [
                f"{domain} near {location}",
                f"best {domain} in {location}",
                f"top {domain} {location}",
            ]
            for query in search_queries:
                print(f" Searching: {query}")
                try:
                    fallback_competitors.extend(_collect_competitors_from_search_query(query, company, location))
                except Exception:
                    print(f"  [!] Search query failed: {query}")
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
                    print(f"  [!] Second-pass search: {query}")
                    try:
                        for row in _collect_competitors_from_search_query(query, company, location):
                            n = row.get("name", "").strip()
                            if n and n not in seen_names:
                                seen_names.add(n)
                                unique_competitors.append(row)
                    except Exception:
                        print(f"  [!] Second-pass query failed: {query}")
                        continue

            if len(unique_competitors) < 6:
                print(
                    f"  [!] Only {len(unique_competitors)} real competitors found. Report will cover available competitors only."
                )

            shared_data["competitor_list"] = unique_competitors
            shared_data["competitor_count"] = len(unique_competitors)
            print(f"  [!] Fallback enriched list: {shared_data['competitor_count']} competitors (real names only)")

    # ── Cap competitors to 4 to prevent token overload in downstream agents ─────
    MAX_COMPETITORS = 4
    if len(shared_data["competitor_list"]) > MAX_COMPETITORS:
        print(f"  [!] Capping competitor list from {len(shared_data['competitor_list'])} to {MAX_COMPETITORS}")
        shared_data["competitor_list"] = shared_data["competitor_list"][:MAX_COMPETITORS]
        shared_data["competitor_count"] = MAX_COMPETITORS

    # Build structured competitor list for explicit injection into prompts
    # (uses the already-capped shared_data["competitor_list"])
    competitor_names = [comp["name"] for comp in shared_data["competitor_list"] if comp.get("name")]
    competitor_list_str = "\n".join(f"- {name}" for name in competitor_names)
    if competitor_names:
        competitor_prompt_addition = (
            f"\n\nDiscovered competitors (analyze every business listed — there are {len(competitor_names)}):\n"
            f"{competitor_list_str}"
        )
    else:
        competitor_prompt_addition = "\n\nNo structured competitor list was extracted; infer competitors from the context and search results."

    # ── Step 2: Product & Service Analysis (chunked for reliability) ──────────────
    print("\n Step 2/7: Product & Service Analysis")
    all_product_results = []

    # Process competitors in batches of 6 to prevent token limits and ensure completion
    BATCH_SIZE = 6
    competitor_batches = [
        competitor_names[i:i + BATCH_SIZE]
        for i in range(0, len(competitor_names), BATCH_SIZE)
    ]

    for batch_num, batch in enumerate(competitor_batches, 1):
        batch_list_str = "\n".join(f"- {name}" for name in batch)
        batch_instruction = (
            f"\n\nBATCH {batch_num}/{len(competitor_batches)} - Analyze these businesses:\n"
            f"{batch_list_str}\n\n"
            f"Focus on: menu items, specialties, unique offerings, ambiance, customer experience.\n"
            f"Use ### headers for each business. Produce at least 200 words of analysis content."
        )

        _result = run_step(
            f"Product & Service Analysis (Batch {batch_num}/{len(competitor_batches)})",
            product_analysis_agent(),
            f"{context}{target_analysis_instruction}{canonical_data_injection}{batch_instruction}",
            company=company,
            domain=domain,
            location=location,
        )
        if _result and len(_result.strip()) >= 100:
            all_product_results.append(_result)
            print(f"  [+] Batch {batch_num} complete ({len(_result)} chars)")
        else:
            print(f"  [!] Batch {batch_num} returned empty, trying fallback...")
            # Fallback for this batch using discovery data
            fallback_prompt = f"""Based on this data, create product analysis for: {', '.join(batch)}

{step_results.get('discovery', 'No discovery data available')}

Analyze core offerings, specialties, and competitive positioning. Use markdown format."""
            _fallback = run_step(
                f"Product Analysis Fallback (Batch {batch_num})",
                product_analysis_agent(),
                fallback_prompt,
                company=company,
                domain=domain,
                location=location,
            )
            if _fallback and len(_fallback.strip()) >= 100:
                all_product_results.append(_fallback)
                print(f"  [+] Batch {batch_num} fallback complete ({len(_fallback)} chars)")

    if all_product_results:
        step_results["product"] = "\n\n---\n\n".join(all_product_results)
        print(f"  [+] Product & Service Analysis complete (total: {len(step_results['product'])} chars)")
    else:
        step_results["product"] = ""
        print("  [!] Product Analysis failed - using empty placeholder")

    # ── Step 3: Pricing & Business Model ──────────────────────────────────────
    print("\nStep 3/7: Pricing & Business Model Analysis")
    _result = run_step(
        "Pricing Analysis",
        pricing_business_agent(),
        f"{context}{target_analysis_instruction}{canonical_data_injection}{competitor_prompt_addition}\n\n"
        f"Analyze pricing and business model for {company} and all discovered local competitors in {location}.",
        company=company,
        domain=domain,
        location=location,
        min_content_length=500,
    )
    if _result is None:
        step_results["pricing"] = ""
        print("  [!] Pricing Analysis skipped — using empty placeholder")
    else:
        step_results["pricing"] = _result
    
    # Extract target company's price position only from its own section (not whole pricing doc)
    pricing_text = step_results["pricing"]
    company_section = ""
    section_match = re.search(
        rf'(?:##{{1,4}})[^#\n]*{re.escape(company)}[^#\n]*\n(.*?)(?=\n##|\Z)',
        pricing_text, re.DOTALL | re.IGNORECASE
    )
    if section_match:
        company_section = section_match.group(1)
    else:
        company_section = pricing_text  # fallback to full text

    price_position = "Data not available"
    if '€€€' in company_section:
        price_position = "Premium"
    elif '€€' in company_section:
        price_position = "Mid-range"
    elif '€' in company_section:
        price_position = "Budget"
    elif 'premium' in company_section.lower():
        price_position = "Premium"
    elif 'mid-range' in company_section.lower() or 'mid range' in company_section.lower():
        price_position = "Mid-range"
    elif 'budget' in pricing_text.lower() or 'low-cost' in pricing_text.lower():
        price_position = "Budget"
    shared_data['price_position'] = price_position

    # ── Per-competitor price extraction for positioning matrix ─────────────────
    per_prices = {}
    for comp in competitor_names:
        section_pattern = rf'(?:##{{1,4}})[^#\n]*{re.escape(comp)}[^#\n]*\n(.*?)(?=\n##|\Z)'
        section_match = re.search(section_pattern, pricing_text, re.DOTALL | re.IGNORECASE)
        if section_match:
            section_text = section_match.group(1)
            if '€€€' in section_text or 'premium' in section_text.lower():
                per_prices[comp] = 'Premium'
            elif '€€' in section_text or 'mid' in section_text.lower():
                per_prices[comp] = 'Mid-range'
            elif '€' in section_text or 'budget' in section_text.lower():
                per_prices[comp] = 'Budget'
    shared_data['per_competitor_prices'] = per_prices
    print(f"  Per-competitor prices extracted: {per_prices}")

    # ── Step 4: Local SEO & Content ────────────────────────────────────────────────
    print("\nStep 4/7: Local SEO & Content Strategy")
    _result = run_step(
        "Local SEO Analysis",
        seo_content_agent(),
        f"{context}{target_analysis_instruction}{competitor_prompt_addition}\n\n"
        f"Analyze local SEO presence and content strategy for {company} and all competitors in {location}.",
        company=company,
        domain=domain,
        location=location,
    )
    if _result is None:
        step_results["seo"] = ""
        print("  [!] SEO Analysis skipped — using empty placeholder")
    else:
        step_results["seo"] = _result

    # YouTube API supplement (if configured) — fetched BEFORE Step 5 so it can be injected into the social prompt
    if YOUTUBE_AVAILABLE and not args.skip_youtube:
        print("   Fetching YouTube stats via API...")
        key_competitors = competitors_seed.split(",") + [company]
        for comp in key_competitors[:5]:
            comp = comp.strip()
            if comp:
                youtube_data[comp] = get_youtube_channel_stats(comp)
                print(f"     YouTube data for {comp}: {youtube_data[comp].get('subscribers', 'N/A')} subscribers")

    # ── Step 5: Social Media Intelligence ────────────────────────────────────────
    print("\nStep 5/7: Social Media Intelligence")
    yt_summary = ""
    if youtube_data:
        lines = ["YouTube API Data (authoritative — use these counts):"]
        for comp, data in youtube_data.items():
            if "error" not in data:
                lines.append(
                    f"  - {comp}: {data.get('subscribers','N/A')} subscribers, "
                    f"{data.get('total_videos','N/A')} videos"
                )
        yt_summary = "\n".join(lines)
    _result = run_step(
        "Social Media Analysis",
        social_media_agent(),
        f"{context}{target_analysis_instruction}{canonical_data_injection}{competitor_prompt_addition}\n\n"
        f"{yt_summary}\n\n"
        f"Analyze social media presence for {company} and all local competitors in {location}."
        f" Focus on local platforms and community engagement.",
        company=company,
        domain=domain,
        location=location,
        min_content_length=500,  # Require at least 500 chars - retry if too short
    )
    if _result is None:
        step_results["social"] = ""
        print("  [!] Social Media Analysis skipped — using empty placeholder")
    else:
        step_results["social"] = _result
    
    # ── Step 6: Local News & Intelligence ────────────────────────────────────────
    print("\nStep 6/7: Local News & Market Intelligence")
    _result = run_step(
        "Local News Analysis",
        news_intelligence_agent(),
        f"{context}{target_analysis_instruction}{competitor_prompt_addition}\n\n"
        f"Find recent local news, events, and developments for {company} and competitors in {location}."
        f" Focus on last 3-6 months of local business activity.",
        company=company,
        domain=domain,
        location=location,
    )
    if _result is None:
        step_results["news"] = ""
        print("  [!] News Analysis skipped — using empty placeholder")
    else:
        step_results["news"] = _result

    # ── Step 7: Customer Feedback ─────────────────────────────────────────────
    print("\nStep 7/7: Customer Feedback Analysis")
    _result = run_step(
        "Customer Feedback",
        customer_feedback_agent(),
        f"{context}{target_analysis_instruction}{canonical_data_injection}{competitor_prompt_addition}\n\n"
        f"Mine customer reviews from Google, Yelp, TripAdvisor for {company} and all local competitors in {location}.",
        company=company,
        domain=domain,
        location=location,
        min_content_length=500,
    )
    if _result is None:
        step_results["feedback"] = ""
        print("  [!] Customer Feedback skipped — using empty placeholder")
    else:
        step_results["feedback"] = _result
    
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
    
    print(f"   Extracted Google review data for {len(shared_data['google_reviews'])} competitors")

    # ── Update canonical_reviews with fresh feedback data (only for missing competitors) ──
    # New data from feedback only fills gaps — discovery data takes precedence
    for competitor_name, review_data in shared_data['google_reviews'].items():
        if competitor_name not in shared_data['canonical_reviews']:
            rating = review_data.get('rating', '')
            count = review_data.get('count', '')
            shared_data['canonical_reviews'][competitor_name] = {
                'rating': rating,
                'count': count,
                'source': 'feedback'
            }

    # ── SWOT Synthesis ────────────────────────────────────────────────
    print("\nBonus: SWOT Analysis & Strategic Recommendations")
    
    competitor_count = shared_data.get('competitor_count')
    competitor_list = shared_data.get('competitor_list')

    # Guard: only skip SWOT if competitor data is completely missing
    # Empty strings from failed steps are tolerated — SWOT can synthesize partial data
    if not competitor_count or not competitor_list:
        step_results["swot"] = "Insufficient data for SWOT analysis – competitor discovery failed."
        print("  [!] SWOT analysis skipped due to insufficient competitor data")
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

        # Build explicit competitor ratings list for SWOT agent
        competitor_ratings_list = []
        for comp in shared_data.get('competitor_list', []):
            name = comp.get('name', '')
            if not name:
                continue
            rev_data = shared_data.get('google_reviews', {}).get(name, {})
            rating = rev_data.get('rating', 'N/A')
            count = rev_data.get('count', 'N/A')
            competitor_ratings_list.append(f"- {name}: Rating {rating} ({count} reviews)")

        if competitor_ratings_list:
            swot_context += "\n\n**Explicit Competitor List with Ratings:**\n" + "\n".join(competitor_ratings_list)

        step_results["swot"] = run_step(
            "SWOT Analysis",
            swot_synthesis_agent(),
            swot_context,
            company=company,
            domain=domain,
            location=location,
            min_content_length=300,
        )
        if step_results["swot"] is None:
            step_results["swot"] = ""

    # ── Advanced Sections (if enabled) ────────────────────────────────────────
    advanced_sections = {}
    if ENABLE_ADVANCED_SECTIONS:
        print("\nAdvanced: Strategic Analysis & Recommendations")
        # Use explicit dict with .format_map() to avoid KeyError on special characters
        advanced_context_kwargs = {
            'company': company,
            'domain': domain,
            'location': location,
            'discovery': clean_cutoff(step_results['discovery'], max_chars=ADVANCED_DISCOVERY_MAX),
            'product': clean_cutoff(step_results['product'], max_chars=ADVANCED_CONTEXT_SECTION_MAX),
            'pricing': clean_cutoff(step_results['pricing'], max_chars=ADVANCED_CONTEXT_SECTION_MAX),
            'seo': clean_cutoff(step_results['seo'], max_chars=ADVANCED_CONTEXT_SECTION_MAX),
            'social': clean_cutoff(step_results['social'], max_chars=ADVANCED_CONTEXT_SECTION_MAX),
            'news': clean_cutoff(step_results['news'], max_chars=ADVANCED_CONTEXT_SECTION_MAX),
            'feedback': clean_cutoff(step_results['feedback'], max_chars=ADVANCED_FEEDBACK_MAX),
            'swot': clean_cutoff(step_results['swot'], max_chars=ADVANCED_CONTEXT_SECTION_MAX),
        }
        advanced_context = """CRITICAL: Generate ALL 9 sections below. Use ### headers exactly matching:
'### 1. Customer Personas', '### 2. Risk Assessment', '### 3. Actionable Recommendations',
'### 4. Financial Benchmarks', '### 5. Digital Ads & Paid Media', '### 6. UGC & Hashtag Analysis',
'### 7. Accessibility & Inclusivity', '### 8. Seasonal Trends', '### 9. Next Steps / Action Plan'.
Do NOT use #### or deeper nesting for section titles.

Business: {company} | Type: {domain} | Location: {location}

Complete Research Summary:
- Discovery: {discovery}
- Product: {product}
- Pricing: {pricing}
- SEO: {seo}
- Social: {social}
- News: {news}
- Feedback: {feedback}
- SWOT: {swot}"""

        # Use .replace() to avoid KeyError from curly braces in content
        advanced_context = (
            advanced_context.replace('{company}', company)
            .replace('{domain}', domain)
            .replace('{location}', location)
            .replace('{discovery}', advanced_context_kwargs['discovery'])
            .replace('{product}', advanced_context_kwargs['product'])
            .replace('{pricing}', advanced_context_kwargs['pricing'])
            .replace('{seo}', advanced_context_kwargs['seo'])
            .replace('{social}', advanced_context_kwargs['social'])
            .replace('{news}', advanced_context_kwargs['news'])
            .replace('{feedback}', advanced_context_kwargs['feedback'])
            .replace('{swot}', advanced_context_kwargs['swot'])
        )
        advanced_result = run_step(
            "Advanced Strategic Analysis",
            advanced_sections_agent(),
            advanced_context,
            company=company,
            domain=domain,
            location=location,
            min_content_length=300,
        )
        if advanced_result is None:
            advanced_result = ""
            print("  [!] Advanced Analysis failed -- using empty placeholder")
        sections = {}
        current_section = None
        current_content = []
        for line in advanced_result.split('\n'):
            if re.match(r'^#{2,5}\s', line):
                if current_section:
                    canonical_key = map_advanced_header_to_canonical_key(current_section)
                    sections[canonical_key] = '\n'.join(current_content)
                current_section = re.sub(r'^#+\s*', '', line).strip()
                current_content = []
            else:
                current_content.append(line)
        if current_section:
            canonical_key = map_advanced_header_to_canonical_key(current_section)
            sections[canonical_key] = '\n'.join(current_content)
        advanced_sections = sections
        print(f"  Advanced section keys: {sorted(advanced_sections.keys())}")
        print(f"  Advanced sections parsed: {list(advanced_sections.keys())}")

    # ── Build Final Report ────────────────────────────────────────────────────
    print("\nBuilding final report...")
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
    print(f"  Analysis Complete!")
    print(f"  Report saved -> {path}")
    print(f"  Total: {len(final_report):,} chars | {len(final_report.split(chr(10)))} lines")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()