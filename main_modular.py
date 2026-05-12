#!/usr/bin/env python3
"""
Competitor Analysis Agent - Modular Version
Fixes: Social media scraping, report quality, Crawl4AI integration

Usage:
  python main_modular.py --company "Stripe" --domain "payment processing" --initial_competitors "Braintree, PayPal"
"""

import argparse
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
from agent.report_generator import synthesize_final_report, save_report


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
    print("  � Platforms: Google, Yelp, TripAdvisor, Instagram, Facebook")
    
    if AGENT_REACH_AVAILABLE:
        print("  � Enhanced Platform Access: Social media insights")
    else:
        print("  ⚠️  To enable enhanced platform access:")
        print("       Install: https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md")
    print("\n")


def run_step(step_name: str, agent, prompt: str) -> str:
    """Run a single agent step with error handling."""
    print(f"  ⏳ {step_name}...")
    try:
        result = agent.run(prompt)
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
        f" Start with these known competitors: {competitors_seed}, then find more local businesses."
    )
    
    # Extract competitor count using regex from discovery output
    import re
    count_match = re.search(r"(\d+)\s*(?:competitors|key players)", step_results['discovery'], re.IGNORECASE)
    
    # Parse competitor data from table rows for competitor_list
    discovery_lines = step_results['discovery'].split('\n')
    table_rows = [line for line in discovery_lines if line.strip().startswith('|') and '---' not in line]
    
    competitors = []
    for row in table_rows[1:]:  # Skip header row
        if row.strip():
            columns = [col.strip() for col in row.split('|')]
            if len(columns) >= 5:
                # Extract name, address, rating, review count from table columns
                # Assuming table format: | Name | Address | Rating | Review Count | ... |
                competitor = {
                    'name': columns[1] if len(columns) > 1 else '',
                    'address': columns[2] if len(columns) > 2 else '',
                    'rating': columns[3] if len(columns) > 3 else '',
                    'review_count': columns[4] if len(columns) > 4 else ''
                }
                if competitor['name'] and competitor['name'] != company:
                    competitors.append(competitor)
    
    shared_data['competitor_list'] = competitors
    
    # Set competitor_count from regex or fallback to parsed list length
    if count_match:
        shared_data['competitor_count'] = int(count_match.group(1))
    else:
        shared_data['competitor_count'] = len(competitors)
    
    print(f"  📊 Discovered {shared_data['competitor_count']} competitors (excluding {company})")
    
    # Check if discovery failed or has insufficient competitors, then use deterministic fallback
    if 'Error:' in step_results['discovery'] or shared_data['competitor_count'] < 6:
        print(f"  🔄 Discovery failed or insufficient competitors. Running deterministic fallback...")
        
        # Import search tools directly
        from agent.tools import TavilyTools, SerperTools
        
        # Use search_tools() directly to run fallback queries
        search_queries = [
            f"{domain} near {location}",
            f"best {domain} in {location}",
            f"top {domain} {location}"
        ]
        
        fallback_competitors = []
        for query in search_queries:
            print(f"  🔍 Searching: {query}")
            try:
                # Try Tavily first, then Serper
                tavily_results = TavilyTools().search(query)
                if tavily_results and hasattr(tavily_results, 'results'):
                    for result in tavily_results.results[:3]:  # Top 3 results per query
                        if hasattr(result, 'title') and result.title:
                            competitor = {
                                'name': result.title,
                                'address': getattr(result, 'address', ''),
                                'rating': getattr(result, 'rating', ''),
                                'review_count': getattr(result, 'reviews', '')
                            }
                            if competitor['name'] and competitor['name'] != company:
                                fallback_competitors.append(competitor)
                else:
                    # Fallback to Serper
                    serper_results = SerperTools().search(query)
                    if serper_results and hasattr(serper_results, 'organic'):
                        for result in serper_results.organic[:3]:  # Top 3 results per query
                            if hasattr(result, 'title') and result.title:
                                competitor = {
                                    'name': result.title,
                                    'address': getattr(result, 'address', ''),
                                    'rating': getattr(result, 'rating', ''),
                                    'review_count': getattr(result, 'reviews', '')
                                }
                                if competitor['name'] and competitor['name'] != company:
                                    fallback_competitors.append(competitor)
            except Exception as e:
                print(f"  ⚠️  Search query failed: {query}")
                continue
        
        # Deduplicate competitors by name
        unique_competitors = []
        seen_names = set()
        for comp in fallback_competitors:
            if comp['name'] not in seen_names:
                unique_competitors.append(comp)
                seen_names.add(comp['name'])
        
        # Ensure at least 6 competitors
        if len(unique_competitors) < 6:
            print(f"  ⚠️  Fallback found only {len(unique_competitors)} competitors. Adding generic entries to reach minimum.")
            # Add generic entries if needed
            for i in range(len(unique_competitors), 6):
                unique_competitors.append({
                    'name': f'Local Competitor {i+1}',
                    'address': f'{location} Area',
                    'rating': 'N/A',
                    'review_count': 'N/A'
                })
        
        # Update shared_data with fallback results
        shared_data['competitor_list'] = unique_competitors[:6]  # Limit to 6
        shared_data['competitor_count'] = len(shared_data['competitor_list'])
        print(f"  📊 Fallback discovered {shared_data['competitor_count']} competitors (excluding {company})")
    
    # Build structured competitor list from shared_data for explicit injection into prompts
    competitor_names = [comp['name'] for comp in shared_data['competitor_list'] if comp.get('name')]
    competitor_list_str = "\n".join(f"- {name}" for name in competitor_names)
    competitor_prompt_addition = f"\n\nDiscovered competitors (MUST analyze every single one):\n{competitor_list_str}"

    # ── Step 2: Product & Service Analysis ──────────────────────────────────────
    print("\n🔬 Step 2/7: Product & Service Analysis")
    step_results["product"] = run_step(
        "Product & Service Analysis",
        product_analysis_agent(),
        f"{context}{competitor_prompt_addition}\n\n"
        f"Now do deep product/service analysis for each competitor vs {company} in {location}."
    )

    # ── Step 3: Pricing & Business Model ──────────────────────────────────────
    print("\n💰 Step 3/7: Pricing & Business Model Analysis")
    step_results["pricing"] = run_step(
        "Pricing Analysis",
        pricing_business_agent(),
        f"{context}{competitor_prompt_addition}\n\n"
        f"Analyze pricing and business model for {company} and all discovered local competitors in {location}."
    )
    
    # Extract price position from pricing output
    pricing_text = step_results["pricing"]
    price_position = "Data not available"
    # Check for € symbols (€, €€, €€€)
    if '€€€' in pricing_text:
        price_position = "Premium"
    elif '€€' in pricing_text:
        price_position = "Mid-range"
    elif '€' in pricing_text:
        price_position = "Budget"
    # Check for text-based price position
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
        f"Analyze local SEO presence and content strategy for {company} and all competitors in {location}."
    )

    # ── Step 5: Social Media Intelligence ────────────────────────────────────────
    print("\n📱 Step 5/7: Social Media Intelligence")
    step_results["social"] = run_step(
        "Social Media Analysis",
        social_media_agent(),
        f"{context}{competitor_prompt_addition}\n\n"
        f"Analyze social media presence for {company} and all local competitors in {location}."
        f" Focus on local platforms and community engagement."
    )
    
    # YouTube API supplement (if configured)
    if YOUTUBE_AVAILABLE and not args.skip_youtube:
        print("  🎬 Fetching YouTube stats via API...")
        # Get competitors from discovery (simplified — extract company names)
        key_competitors = competitors_seed.split(",") + [company]
        for comp in key_competitors[:5]:  # Limit to avoid quota
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
        f" Focus on last 3-6 months of local business activity."
    )

    # ── Step 7: Customer Feedback ─────────────────────────────────────────────
    print("\n💬 Step 7/7: Customer Feedback Analysis")
    step_results["feedback"] = run_step(
        "Customer Feedback",
        customer_feedback_agent(),
        f"{context}{competitor_prompt_addition}\n\n"
        f"Mine customer reviews from Google, Yelp, TripAdvisor for {company} and all local competitors in {location}."
    )
    
    # Extract Google review counts and ratings from feedback output
    import re
    import json
    feedback_text = step_results['feedback']
    
    # First, try to extract from Google Maps Scraper JSON output
    if GOOGLE_MAPS_SCRAPER_AVAILABLE:
        # Look for JSON blocks in the output
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
    
    # Fallback: extract from text using regex (handles search tool fallback)
    # Pattern for "X.X/5 (N reviews)" or "X.X stars N reviews"
    rating_count_pattern = r'([A-Za-z\s]+?)[\s:]+(\d+\.?\d*)[/\s]*(?:5|stars)[\s\(\)]+(\d+)\s+reviews'
    for match in re.finditer(rating_count_pattern, feedback_text, re.IGNORECASE):
        competitor_name = match.group(1).strip()
        rating = float(match.group(2))
        review_count = int(match.group(3))
        # Only add if not already extracted from scraper
        if competitor_name not in shared_data['google_reviews']:
            shared_data['google_reviews'][competitor_name] = {'rating': rating, 'count': review_count}
    
    # Additional fallback: extract rating and count separately if combined pattern doesn't match
    for competitor in shared_data['competitor_list']:
        competitor_name = competitor['name']
        if competitor_name not in shared_data['google_reviews']:
            # Try to find rating for this competitor
            rating_match = re.search(rf'{re.escape(competitor_name)}[^\n]*?(\d+\.?\d*)[/\s]*(?:5|stars)', feedback_text, re.IGNORECASE)
            count_match = re.search(rf'{re.escape(competitor_name)}[^\n]*?(\d+)\s+reviews', feedback_text, re.IGNORECASE)
            
            rating = float(rating_match.group(1)) if rating_match else None
            count = int(count_match.group(1)) if count_match else None
            
            if rating or count:
                shared_data['google_reviews'][competitor_name] = {'rating': rating, 'count': count}
    
    print(f"  📊 Extracted Google review data for {len(shared_data['google_reviews'])} competitors")

    # ── SWOT Synthesis ────────────────────────────────────────────────
    print("\n🎯 Bonus: SWOT Analysis & Strategic Recommendations")
    
    # Guard: Check if competitor discovery succeeded
    competitor_count = shared_data.get('competitor_count')
    competitor_list = shared_data.get('competitor_list')
    
    # Check that competitor_count is an integer and > 0, and competitor_list is non-empty
    if not isinstance(competitor_count, int) or competitor_count is None or competitor_count <= 0 or not competitor_list or (isinstance(competitor_list, list) and len(competitor_list) == 0):
        step_results["swot"] = "Insufficient data for SWOT analysis – competitor discovery failed."
        print("  ⚠️  SWOT analysis skipped due to insufficient competitor data")
    else:
        swot_context = f"""
Business: {company} | Type: {domain} | Location: {location}
Competitor Count: {shared_data['competitor_count']}

Key Local Research Findings:
- Local Competitor Discovery: {step_results['discovery'][:1500]}
- Product & Service Analysis: {step_results['product'][:1500]}
- Pricing & Business Model: {step_results['pricing'][:1000]}
- Customer Feedback: {step_results['feedback'][:1000]}
- Local News & Events: {step_results['news'][:800]}
"""
        step_results["swot"] = run_step(
            "SWOT Analysis",
            swot_synthesis_agent(),
            swot_context
        )

    # ── Advanced Sections (if enabled) ────────────────────────────────────────
    advanced_sections = {}
    if ENABLE_ADVANCED_SECTIONS:
        print("\n🚀 Advanced: Strategic Analysis & Recommendations")
        advanced_context = f"""
Business: {company} | Type: {domain} | Location: {location}

Complete Research Summary:
- Discovery: {step_results['discovery'][:1000]}
- Product: {step_results['product'][:1000]}
- Pricing: {step_results['pricing'][:800]}
- SEO: {step_results['seo'][:800]}
- Social: {step_results['social'][:800]}
- News: {step_results['news'][:600]}
- Feedback: {step_results['feedback'][:1000]}
- SWOT: {step_results['swot'][:1000]}
"""
        advanced_result = run_step(
            "Advanced Strategic Analysis",
            advanced_sections_agent(),
            advanced_context
        )
        # Parse the advanced result into sections (simple parsing based on headers)
        sections = {}
        current_section = None
        current_content = []
        for line in advanced_result.split('\n'):
            if line.startswith('###') or line.startswith('##'):
                if current_section:
                    sections[current_section.lower().replace(' ', '_')] = '\n'.join(current_content)
                current_section = line.strip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        if current_section:
            sections[current_section.lower().replace(' ', '_')] = '\n'.join(current_content)
        advanced_sections = sections

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
