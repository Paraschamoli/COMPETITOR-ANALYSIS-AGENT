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
    AGENT_REACH_AVAILABLE, YOUTUBE_AVAILABLE, ENABLE_ADVANCED_SECTIONS
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
    print(f"  YouTube API    : {'✅ Configured' if YOUTUBE_AVAILABLE else '❌ Not configured (add YOUTUBE_API_KEY to .env)'}")
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
        print(f"  ❌ {step_name} failed: {e}")
        return f"[{step_name} failed: {e}]"


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
    
    # Extract competitor count from discovery output
    discovery_lines = step_results['discovery'].split('\n')
    table_rows = [line for line in discovery_lines if line.strip().startswith('|') and '---' not in line]
    shared_data['competitor_count'] = max(0, len(table_rows) - 2)
    print(f"  📊 Discovered {shared_data['competitor_count']} competitors (excluding {company})")

    # ── Step 2: Product & Service Analysis ──────────────────────────────────────
    print("\n🔬 Step 2/7: Product & Service Analysis")
    step_results["product"] = run_step(
        "Product & Service Analysis",
        product_analysis_agent(),
        f"{context}\n\nDiscovered local competitors:\n{step_results['discovery'][:2000]}\n\n"
        f"Now do deep product/service analysis for each competitor vs {company} in {location}."
    )

    # ── Step 3: Pricing & Business Model ──────────────────────────────────────
    print("\n💰 Step 3/7: Pricing & Business Model Analysis")
    step_results["pricing"] = run_step(
        "Pricing Analysis",
        pricing_business_agent(),
        f"{context}\n\nAnalyze pricing and business model for {company} and all discovered local competitors in {location}."
    )

    # ── Step 4: Local SEO & Content ────────────────────────────────────────────────
    print("\n🔍 Step 4/7: Local SEO & Content Strategy")
    step_results["seo"] = run_step(
        "Local SEO Analysis",
        seo_content_agent(),
        f"{context}\n\nAnalyze local SEO presence and content strategy for {company} and all competitors in {location}."
    )

    # ── Step 5: Social Media Intelligence ────────────────────────────────────────
    print("\n📱 Step 5/7: Social Media Intelligence")
    step_results["social"] = run_step(
        "Social Media Analysis",
        social_media_agent(),
        f"{context}\n\nAnalyze social media presence for {company} and all local competitors in {location}."
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
        f"{context}\n\nFind recent local news, events, and developments for {company} and competitors in {location}."
        f" Focus on last 3-6 months of local business activity."
    )

    # ── Step 7: Customer Feedback ─────────────────────────────────────────────
    print("\n💬 Step 7/7: Customer Feedback Analysis")
    step_results["feedback"] = run_step(
        "Customer Feedback",
        customer_feedback_agent(),
        f"{context}\n\nMine customer reviews from Google, Yelp, TripAdvisor for {company} and all local competitors in {location}."
    )
    
    # Extract Google review counts from feedback output
    import re
    feedback_text = step_results['feedback']
    for match in re.finditer(r'([A-Za-z\s]+?)[\s:]+(\d+)\s+reviews', feedback_text, re.IGNORECASE):
        competitor_name = match.group(1).strip()
        review_count = int(match.group(2))
        shared_data['google_reviews'][competitor_name] = review_count
    print(f"  📊 Extracted Google review counts for {len(shared_data['google_reviews'])} competitors")

    # ── SWOT Synthesis ────────────────────────────────────────────────────────
    print("\n🎯 Bonus: SWOT Analysis & Strategic Recommendations")
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
