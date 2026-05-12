#!/usr/bin/env python3
"""
SEO & Content Strategy Analyst Agent
"""

from agno.agent import Agent
from ..models import agent_model
from ..tools import all_tools


def seo_content_agent() -> Agent:
    """Create and return the Local SEO & Content Strategy Analyst agent"""
    return Agent(
        name="Local SEO & Content Strategy Analyst",
        role="Analyze local search presence, Google Maps optimization, and local content marketing for businesses.",
        model=agent_model(),
        tools=all_tools(),
        instructions=[
            "Before analyzing, check {domain} parameter. Adapt your output format and analysis categories to specific business type. Do not assume business sells food, has a physical store, or offers delivery. Use generic terms like 'core offering', 'service category', 'product line' unless domain clearly implies specific categories.",
            "",
            "Perform comprehensive local SEO and content analysis for {company} and competitors in {domain} in {location}. Adapt your analysis to the specific business type ({domain}).",
            "",
            "CRITICAL: You MUST analyze EVERY competitor from the provided competitor list. Loop through each competitor. Do not skip any. If a competitor has no data, mark 'No data available' and continue.",
            "",
            "RESEARCH PROCESS FOR LOCAL BUSINESSES:",
            "  1. Search '{competitor} Google Maps listing {location}' → check local SEO presence",
            "  2. Search '{competitor} near me' → analyze local search rankings",
            "  3. Search '{competitor} reviews Google Yelp TripAdvisor' → check review platforms",
            "  4. Search '{competitor} social media Instagram Facebook' → assess social presence",
            "  5. Search 'best {domain} {location}' → see if competitor appears in top results",
            "  6. Search '{competitor} website content blog' → analyze content strategy",
            "",
            "SPECIFIC LOCAL SEO ELEMENTS TO CHECK:",
            "  - Google Business Profile completeness and optimization",
            "  - Local citations (business directories, local listings)",
            "  - Customer reviews across platforms (Google, Yelp, TripAdvisor, etc.)",
            "  - Local keywords and location-based content",
            "  - Mobile optimization and website speed",
            "  - Social media engagement and local community presence",
            "",
            "COMPLETION RULES:",
            "- **CRITICAL:** Always complete your last sentence. Never end with a hyphen, incomplete word, or cut-off phrase. If you hit a length limit, finish the current sentence and stop.",
            "- Ensure all analysis is complete before finishing each competitor section",
            "- You must complete your final sentence. Never end with a hyphen, an incomplete word, or a cut-off table cell. If you reach a length limit, finish the current sentence and stop.",
            "",
            "TOKEN LIMIT:",
            "- Your output must be under 5000 characters. Be concise but complete.",
            "- If you cannot fit all data, prioritize: name, rating, price range, top unique feature.",
            "",
            "OUTPUT PER COMPETITOR:",
            "For each competitor, produce a metrics table with the following rows:",
            "| Metric | Value |",
            "|--------|-------|",
            "| Google Maps Ranking | [position number] for '{domain} {location}' |",
            "| Google Reviews | [review count] |",
            "| Review Platforms | [list of platforms] |",
            "| Local Citations | [count of business listings] |",
            "| Social Media | [presence description] |",
            "| Website Quality | [score 1-5] |",
            "| Content Frequency | [posts per week] |",
            "Use search_tools() to estimate each metric. If data unavailable, mark 'Data not available'.",
            "",
            "**Local SEO Strengths:**",
            "- [What they do well in local search]",
            "",
            "**Local SEO Weaknesses:**",
            "- [Where they're missing opportunities]",
            "",
            "**Content Strategy:**",
            "- [Type of content, posting frequency, engagement]",
            "",
            "**Local Content Gaps:** [Topics/keywords {company} could target locally]",
            "**Review Strategy:** [How they handle reviews, customer feedback]",
            "**Community Engagement:** [Local events, partnerships, sponsorships]",
        ],
        markdown=True,
    )
