#!/usr/bin/env python3
"""
Competitor Analysis Agent - Hybrid Team + Workflow Architecture
Powered by: Agno Teams · OpenRouter · Firecrawl · Tavily · Serper

Usage:
  python main.py --domain "payment processing" --initial_competitors "Stripe, Braintree"
"""

import argparse
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv
import json

load_dotenv()

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.team import Team
from agno.workflow import Workflow
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.tavily import TavilyTools
from agno.tools.serper import SerperTools
from agno.tools.firecrawl import FirecrawlTools

# ── model config ──────────────────────────────────────────────────────────────

COORDINATOR_MODEL = "openai/gpt-5.4"

AGENT_MODEL       = "openai/gpt-5.4"

def coordinator_model():
    return OpenRouter(id=COORDINATOR_MODEL)

def agent_model():
    return OpenRouter(id=AGENT_MODEL)

# ── tools ─────────────────────────────────────────────────────────────────────

def search_tools():
    """Both Tavily and Serper for comprehensive search coverage."""
    return [TavilyTools(), SerperTools()]

def crawl_tools():
    """Firecrawl — direct scrape of competitor pages into clean Markdown."""
    return FirecrawlTools()

# ── workflow step agents ─────────────────────────────────────────────────────

def competitor_discovery_agent() -> Agent:
    return Agent(
        name="Competitor Discovery Specialist",
        role="Identify and analyze comprehensive competitive landscape for target company.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "COMPREHENSIVE COMPETITOR DISCOVERY FOR: {company} in {domain} domain",
            "",
            "PRIMARY TARGET: {company}",
            "Starting point: {initial_competitors}",
            "",
            "RESEARCH METHODOLOGY:",
            "1. Search for '{company} competitors alternatives'",
            "2. Search for 'top {domain} companies platforms solutions'",
            "3. Search for '{company} vs {domain} competitors comparison'",
            "4. Search for '{domain} market leaders analysis reports'",
            "5. Search for '{company} market share competitive landscape'",
            "",
            "COMPETITOR CATEGORIZATION:",
            "- DIRECT COMPETITORS: Same core product/service, same target market",
            "- INDIRECT COMPETITORS: Solve same problem with different approach",
            "- EMERGING COMPETITORS: New entrants, startups, disruptors",
            "- MARKET LEADERS: Established players with significant market share",
            "- NICHE PLAYERS: Specialized solutions for specific segments",
            "",
            "FOR EACH COMPETITOR PROVIDE:",
            "- Company name and founding year",
            "- Detailed description and positioning statement",
            "- Target market and ideal customer profile",
            "- Key products/services and features",
            "- Pricing model and market positioning",
            "- Estimated market size/revenue if available",
            "- Geographic presence and scale",
            "- Notable funding or acquisitions",
            "- Key differentiators vs {company}",
            "",
            "DELIVERABLE: Comprehensive competitive landscape analysis with 8-15 competitors categorized appropriately, focusing on detailed company profiles and market positioning."
        ],
        markdown=True,
    )

def product_analysis_agent() -> Agent:
    return Agent(
        name="Product Analysis Specialist", 
        role="Analyze what each competitor offers including features, value propositions, and target audience.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "COMPREHENSIVE PRODUCT ANALYSIS FOR: {company} and all competitors in {domain} domain",
            "",
            "FOR EACH COMPETITOR INCLUDING {company}:",
            "",
            "1. CORE PRODUCT OFFERINGS:",
            "- Scrape main product/features page directly",
            "- Extract complete feature list with specific names",
            "- Identify product tiers and versions",
            "- Document core value proposition and positioning",
            "",
            "2. FEATURE COMPARISON:",
            "- Search for '{competitor} features capabilities'",
            "- Create detailed feature matrix across all competitors",
            "- Identify unique vs common features",
            "- Note feature depth and sophistication",
            "",
            "3. INTEGRATIONS & ECOSYSTEM:",
            "- Search for '{competitor} integrations API'",
            "- Scrape integrations page for complete list",
            "- Categorize integrations (native, third-party, API)",
            "- Assess ecosystem strength and openness",
            "",
            "4. TARGET MARKET ANALYSIS:",
            "- Identify ideal customer profiles and segments",
            "- Document use cases and applications",
            "- Analyze industry verticals served",
            "- Note company size focus (SMB, mid-market, enterprise)",
            "",
            "5. USER EXPERIENCE & SENTIMENT:",
            "- Search for '{competitor} reviews G2 Capterra TrustRadius'",
            "- Extract specific user quotes and feedback",
            "- Identify common pain points and praise",
            "- Note user satisfaction scores if available",
            "",
            "DELIVERABLE: Detailed product comparison matrix with feature analysis, integration landscape, target market analysis, and user sentiment for all competitors including {company}."
        ],
        markdown=True,
    )

def business_model_agent() -> Agent:
    return Agent(
        name="Business Model Analyst",
        role="Analyze how competitors sell their products and evaluate their sales effectiveness.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "Your task is to analyze competitors' business and sales models.",
            "For each competitor:",
            "1. Identify sales channels: Self-serve, Enterprise sales, Marketplace, Partner network, API-first",
            "2. Analyze their GTM strategy: Product-led growth, Sales-led, Hybrid",
            "3. Look for traction signals: Customer count, Case studies, Testimonials, Funding, Growth metrics",
            "4. Evaluate effectiveness based on public signals",
            "5. Check for pricing page complexity, sales team presence, free trials",
            "Output format: Business model analysis with effectiveness assessment"
        ],
        markdown=True,
    )

def pricing_strategy_agent() -> Agent:
    return Agent(
        name="Pricing Strategy Analyst",
        role="Analyze pricing models, packaging, and how competitors structure their offerings.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "Your task is to analyze competitors' pricing and packaging strategies.",
            "For each competitor:",
            "1. Scrape their pricing page directly",
            "2. Identify pricing model: Subscription, Freemium, Usage-based, Tiered, Enterprise, Custom",
            "3. Analyze plan structure: Free tier limits, Entry pricing, Mid-tier features, Enterprise features",
            "4. Look for hidden costs, setup fees, or usage overages",
            "5. Compare value proposition across tiers",
            "6. Search for '{competitor} pricing reviews' to understand customer perception",
            "Output format: Detailed pricing analysis with plan comparisons"
        ],
        markdown=True,
    )

def digital_marketing_agent() -> Agent:
    return Agent(
        name="Digital Marketing Analyst",
        role="Analyze competitors' digital marketing strategies across platforms and content types.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "Your task is to analyze competitors' digital marketing presence.",
            "For each competitor:",
            "1. Identify active platforms: LinkedIn, Twitter/X, Instagram, YouTube, TikTok, Blog",
            "2. Analyze content strategy: Blog posts, Videos, Reels, Case studies, Webinars, Ads",
            "3. Measure posting patterns: Frequency, timing, consistency",
            "4. Evaluate engagement: Average likes, comments, shares, follower growth",
            "5. Analyze interaction style: Response to comments, tone (formal/casual/promotional)",
            "6. Look for paid advertising presence and content distribution",
            "Output format: Marketing analysis with platform-specific insights"
        ],
        markdown=True,
    )

def customer_feedback_agent() -> Agent:
    return Agent(
        name="Customer Feedback Analyst",
        role="Collect and analyze customer reviews, complaints, and feature requests from public sources.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "Your task is to analyze customer feedback for each competitor.",
            "For each competitor:",
            "1. Search reviews on: G2, Capterra, TrustRadius, Product Hunt, Reddit",
            "2. Look for: '{competitor} reviews', '{competitor} complaints', '{competitor} feature requests'",
            "3. Scrape review pages to get actual customer quotes",
            "4. Identify recurring themes: Pain points, Praise, Feature requests, Support issues",
            "5. Analyze sentiment patterns and customer satisfaction indicators",
            "6. Look for competitor comparisons in reviews",
            "Output format: Structured feedback analysis with quotes and themes"
        ],
        markdown=True,
    )

def swot_analysis_agent() -> Agent:
    return Agent(
        name="SWOT Analysis Specialist",
        role="Synthesize all previous analysis into comprehensive SWOT assessments for each competitor.",
        model=coordinator_model(),
        tools=[],
        instructions=[
            "Your task is to create comprehensive SWOT analyses based on all previous research.",
            "For each competitor, analyze:",
            "STRENGTHS:",
            "- Market position and advantages",
            "- Unique capabilities or features",
            "- Strong customer feedback areas",
            "- Business model strengths",
            "- Marketing effectiveness",
            
            "WEAKNESSES:",
            "- Product limitations or gaps",
            "- Customer complaint patterns",
            "- Pricing or packaging issues",
            "- Market position challenges",
            "- Operational or support issues",
            
            "OPPORTUNITIES:",
            "- Market trends they can leverage",
            "- Underserved customer segments",
            "- Feature gaps they could fill",
            "- Partnership or expansion potential",
            "- Competitive advantages they could build",
            
            "THREATS:",
            "- Competitive pressures",
            "- Market risks or disruptions",
            "- Customer retention risks",
            "- Technology or regulatory changes",
            "- Market saturation challenges",
            
            "Base your analysis on the comprehensive data from all previous workflow steps.",
            "Provide specific, actionable insights for each SWOT category."
        ],
        markdown=True,
    )

# ── Import original agents from main_old.py ───────────────────────────────────

def seo_agent() -> Agent:
    return Agent(
        name="SEO & Traffic Analyst",
        role="Research SEO presence, organic traffic, and keyword strategy for each competitor.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "For each competitor:",
            "  1. Search '<competitor> organic traffic SEO keywords site overview' to find Semrush/SimilarWeb pages.",
            "  2. Firecrawl any found overview page to extract actual metrics.",
            "  3. Also scrape the competitor's blog index page — it reveals their content strategy.",
            "  4. If scraping fails (LinkedIn, Twitter, etc.), rely on search results and mention limitations.",
            "Report per competitor: estimated monthly visits, domain authority (if found), top 5 keywords, content cadence.",
            "Use actual numbers. If data is unavailable, say so explicitly.",
        ],
        markdown=True,
    )

def social_agent() -> Agent:
    return Agent(
        name="Social Media Analyst",
        role="Map social media presence, audience size, and content strategy for each competitor.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "For each competitor:",
            "  1. Search '<competitor> LinkedIn followers Twitter following social media'.",
            "  2. Firecrawl their LinkedIn company page URL if found (linkedin.com/company/...).",
            "  3. Firecrawl their Twitter/X profile if accessible.",
            "  4. If scraping fails (LinkedIn, Twitter blocked), use search results to estimate follower counts and activity.",
            "Report: follower count per platform, posting frequency, content themes, B2B vs B2C tone, any standout campaigns.",
            "Prioritize LinkedIn, Twitter/X, YouTube for B2B. Instagram/TikTok for B2C.",
        ],
        markdown=True,
    )

def news_agent() -> Agent:
    return Agent(
        name="News & Intelligence Analyst",
        role="Track recent news, funding, product launches, and strategic moves.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "For each competitor:",
            "  1. Search '<competitor> news funding launch acquisition 2024 2025'.",
            "  2. Firecrawl their official blog or newsroom/press page to get announcements directly.",
            "Report (last 6 months): funding rounds + amounts, acquisitions, product launches, exec hires/departures, partnerships, controversies.",
            "Flag any development that signals a major strategic pivot with ⚠️.",
        ],
        markdown=True,
    )

def product_agent() -> Agent:
    return Agent(
        name="Product Features Analyst",
        role="Map product capabilities, differentiators, integrations, and real user sentiment.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "For each competitor:",
            "  1. Firecrawl their main features/product page directly.",
            "  2. Search '<competitor> review G2 Capterra' and Firecrawl one review page.",
            "  3. Search '<competitor> integrations' and Firecrawl their integrations page.",
            "Report: core feature set, top 3 differentiators, key integrations, what users love, what users hate (with quotes if possible).",
            "Include actual feature names and integration names — not vague descriptions.",
        ],
        markdown=True,
    )

def pricing_agent() -> Agent:
    return Agent(
        name="Pricing Analyst",
        role="Extract precise pricing models, plan tiers, and pricing strategy.",
        model=agent_model(),
        tools=[search_tools(), crawl_tools()],
        instructions=[
            "For each competitor:",
            "  1. Search '<competitor> pricing plans' to find the pricing page URL.",
            "  2. Firecrawl their pricing page directly — extract exact plan names, prices, limits, and included features.",
            "  3. If pricing is hidden or enterprise-only, search for analyst estimates or community discussions.",
            "Report: pricing model type (flat/usage/per-seat/freemium), plan names + monthly prices, free tier details, what's gated behind enterprise.",
            "Copy actual price points from the page. Flag if pricing is opaque.",
        ],
        markdown=True,
    )

# ── research team ────────────────────────────────────────────────────────────

def research_team() -> Team:
    """Create research team with original specialist agents."""
    return Team(
        name="Competitor Research Team",
        model=coordinator_model(),
        members=[
            seo_agent(),
            social_agent(),
            news_agent(),
            product_agent(),
            pricing_agent(),
        ],
        instructions=[
            "Coordinate comprehensive competitor analysis across all dimensions:",
            "1. SEO & Website Traffic - organic metrics and content strategy",
            "2. Social Media Presence - platform engagement and audience analysis", 
            "3. News & Recent Developments - funding, launches, strategic moves",
            "4. Product Features Comparison - capabilities, differentiators, integrations",
            "5. Pricing Analysis - models, plans, value propositions",
            "Synthesize findings into structured competitive intelligence report."
        ],
        markdown=True,
    )

# ── mixed execution workflow ───────────────────────────────────────────────

def create_mixed_workflow(domain: str, initial_competitors: str) -> Workflow:
    """Create mixed execution pipeline with teams and individual agents."""
    
    return Workflow(
        name="Mixed Execution Pipeline",
        description="Hybrid workflow combining teams and individual agents for comprehensive analysis",
        steps=[
            # Step 1: Competitor Discovery
            {
                "name": "competitor_discovery",
                "agent": competitor_discovery_agent(),
                "input": f"Domain: {domain}\nInitial competitors: {initial_competitors}\n\nDiscover and categorize all relevant competitors in this domain.",
                "output_key": "discovered_competitors"
            },
            
            # Step 2: Research Team Analysis
            {
                "name": "research_team_analysis",
                "agent": research_team(),
                "input": "Analyze competitors: {discovered_competitors} in domain: {domain}\n\nExecute comprehensive research across SEO, social media, news, products, and pricing dimensions.",
                "output_key": "research_findings"
            },
            
            # Step 3: Business Model Analysis
            {
                "name": "business_model_analysis",
                "agent": business_model_agent(),
                "input": "Based on research findings: {research_findings}\n\nAnalyze business models, sales channels, and GTM strategies for each competitor.",
                "output_key": "business_model_analysis"
            },
            
            # Step 4: Digital Marketing Analysis
            {
                "name": "digital_marketing_analysis",
                "agent": digital_marketing_agent(),
                "input": "Extend marketing analysis for: {discovered_competitors}\n\nBuilding on research: {research_findings} and business models: {business_model_analysis}",
                "output_key": "marketing_analysis"
            },
            
            # Step 5: Customer Feedback Analysis
            {
                "name": "customer_feedback_analysis",
                "agent": customer_feedback_agent(),
                "input": "Collect customer feedback for: {discovered_competitors}\n\nConsidering research: {research_findings} and pricing: {business_model_analysis}",
                "output_key": "customer_feedback"
            },
            
            # Step 6: SWOT Analysis
            {
                "name": "swot_analysis",
                "agent": swot_analysis_agent(),
                "input": "Create comprehensive SWOT analysis using all research:\n\nCompetitors: {discovered_competitors}\nResearch: {research_findings}\nBusiness Models: {business_model_analysis}\nMarketing: {marketing_analysis}\nCustomer Feedback: {customer_feedback}",
                "output_key": "swot_analysis"
            }
        ]
    )

# ── final synthesis team ────────────────────────────────────────────────────

def create_synthesis_team() -> Team:
    """Create team to synthesize workflow results into final report."""
    
    coordinator = Agent(
        name="Report Synthesizer",
        role="Synthesize all workflow steps into comprehensive competitor analysis report",
        model=coordinator_model(),
        instructions=[
            "You are creating the final competitor analysis report.",
            "Synthesize all workflow step outputs into a structured, actionable report.",
            "Include:",
            "1. Executive Summary with key findings",
            "2. Detailed analysis from each workflow step",
            "3. Comparative tables and insights",
            "4. Strategic recommendations",
            "5. Actionable next steps",
            "Ensure the report is well-structured, professional, and provides clear competitive intelligence."
        ],
        markdown=True,
    )
    
    return Team(
        name="Competitor Analysis Synthesis Team",
        model=coordinator_model(),
        members=[coordinator],
        instructions=["Synthesize all workflow outputs into comprehensive final report"],
        markdown=True,
    )

# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Competitor Analysis Agent — Hybrid Team + Workflow Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --domain "payment processing" --company "Stripe" --initial_competitors "Braintree"
  python main.py --domain "note-taking apps" --company "Notion" --initial_competitors "Obsidian"
  python main.py --domain "developer hosting" --company "Vercel" --initial_competitors "Netlify"
        """,
    )
    parser.add_argument("--company", required=True,
        help='Target company to analyze: "Stripe"')
    parser.add_argument("--domain", required=True,
        help='Market domain: "payment processing"')
    parser.add_argument("--initial_competitors", required=False,
        help='Optional initial competitors: "Braintree"')
    parser.add_argument("--output", default=None,
        help="Output file path (default: ./output/<auto-named>.md)")
    return parser.parse_args()

def banner(domain: str, company: str, initial_competitors: str):
    w = 80
    print("\n" + "═" * w)
    print("  🔍  COMPETITOR ANALYSIS AGENT - HYBRID WORKFLOW")
    print("═" * w)
    print(f"  Domain              : {domain}")
    print(f"  Initial Competitors : {initial_competitors}")
    print(f"  Coordinator         : {COORDINATOR_MODEL}")
    print(f"  Agents              : {AGENT_MODEL}")
    print(f"  Architecture        : Team + Sequential Workflow (7 steps)")
    print(f"  Tools               : Firecrawl + Tavily + Serper")
    print("═" * w + "\n")

def save_report(content: str, output_path: str | None, domain: str) -> Path:
    if output_path:
        path = Path(output_path)
    else:
        Path("output").mkdir(exist_ok=True)
        slug = domain.replace(" ", "_").replace("/", "_").lower()[:30]
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        path = Path(f"output/competitor_analysis_{slug}_{ts}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path

def main():
    args = parse_args()
    initial_competitors = args.initial_competitors or "Auto-discovered"
    banner(args.domain, args.company, initial_competitors)

    print("Starting Enhanced Mixed Execution Pipeline with Teams + Agents...\n")
    
    # Step 1: Competitor Discovery
    print("Step 1/7: Comprehensive Competitor Discovery...")
    discovery_agent = competitor_discovery_agent()
    discovery_prompt = f"COMPREHENSIVE COMPETITOR DISCOVERY FOR: {args.company} in {args.domain} domain\n\nStarting point: {initial_competitors}\n\nExecute detailed competitive landscape analysis as specified."
    step1_result = discovery_agent.run(discovery_prompt)
    
    # Step 2: Product Analysis (Enhanced)
    print("Step 2/7: Detailed Product Analysis...")
    product_agent = product_analysis_agent()
    product_prompt = f"COMPREHENSIVE PRODUCT ANALYSIS FOR: {args.company} and all discovered competitors in {args.domain} domain\n\nExecute detailed product comparison analysis as specified."
    step2_result = product_agent.run(product_prompt)
    
    # Step 3: Research Team Analysis (using original agents)
    print("Step 3/7: Research Team Analysis...")
    research_team_instance = research_team()
    research_prompt = f"Execute comprehensive research across SEO, social media, news, products, and pricing dimensions for: {args.company} and all competitors in {args.domain} domain."
    step3_result = research_team_instance.run(research_prompt)
    
    # Step 4: Business Model Analysis
    print("Step 4/7: Business Model Analysis...")
    business_agent = business_model_agent()
    business_prompt = f"Based on research findings, analyze business models, sales channels, and GTM strategies for: {args.company} and all competitors in {args.domain} domain."
    step4_result = business_agent.run(business_prompt)
    
    # Step 5: Digital Marketing Analysis
    print("Step 5/7: Digital Marketing Analysis...")
    marketing_agent = digital_marketing_agent()
    marketing_prompt = f"Extend marketing analysis for: {args.company} and all competitors in {args.domain} domain, building on all previous research findings."
    step5_result = marketing_agent.run(marketing_prompt)
    
    # Step 6: Customer Feedback Analysis
    print("Step 6/7: Customer Feedback Analysis...")
    feedback_agent = customer_feedback_agent()
    feedback_prompt = f"Collect customer feedback for: {args.company} and all competitors in {args.domain} domain, considering all previous research findings."
    step6_result = feedback_agent.run(feedback_prompt)
    
    # Step 7: SWOT Analysis
    print("Step 7/7: SWOT Analysis...")
    swot_agent_instance = swot_analysis_agent()
    swot_prompt = f"Create comprehensive SWOT analysis for: {args.company} and all competitors in {args.domain} domain using all previous research findings."
    step7_result = swot_agent_instance.run(swot_prompt)
    
    print("\nSynthesizing comprehensive final report...")
    synthesis_team = create_synthesis_team()
    
    synthesis_prompt = f"""
    Create comprehensive competitor analysis report for {args.company} in the {args.domain} domain.
    
    Enhanced Mixed Execution Pipeline Results:
    1. Competitor Discovery: {step1_result}
    2. Product Analysis: {step2_result}
    3. Research Team Analysis: {step3_result}
    4. Business Model Analysis: {step4_result}
    5. Digital Marketing Analysis: {step5_result}
    6. Customer Feedback: {step6_result}
    7. SWOT Analysis: {step7_result}
    
    Create a highly detailed structured report with:
    1. Executive Summary with key findings and strategic insights
    2. Target Company Analysis ({args.company}) - detailed profile
    3. Comprehensive Competitive Landscape Analysis
    4. Detailed Product Comparison Matrix with feature analysis
    5. Research Team Findings (SEO, Social, News, Products, Pricing)
    6. Business Model Analysis (sales channels, GTM strategies, effectiveness)
    7. Digital Marketing Analysis (platform presence, content strategies, engagement)
    8. Customer Feedback Summary (pain points, praise, feature requests)
    9. SWOT Analysis for all key competitors
    10. Strategic Recommendations (actionable insights and next steps)
    11. Market Positioning Analysis
    12. Competitive Intelligence Summary
    
    Focus on providing highly detailed competitive intelligence with specific data points, metrics, and actionable insights.
    Use extensive comparative tables, charts descriptions, and include specific examples and quotes.
    """
    
    final_report = synthesis_team.run(synthesis_prompt)
    
    # Extract content properly from team result
    if hasattr(final_report, "content"):
        report_content = final_report.content
    elif hasattr(final_report, "data"):
        report_content = final_report.data
    elif isinstance(final_report, str):
        report_content = final_report
    else:
        report_content = str(final_report) if final_report is not None else "Report generation failed - no content returned"
    
    path = save_report(report_content, args.output, f"{args.company}_{args.domain}")
    
    print("\n" + "=" * 80)
    print(f"  Enhanced Mixed Execution Pipeline Complete!")
    print(f"  Report saved -> {path}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
