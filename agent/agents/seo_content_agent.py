#!/usr/bin/env python3
"""
SEO & Content Strategy Analyst Agent
"""

from agno.agent import Agent
from ..models import agent_model
from ..tools import all_tools
from ..shared_instructions import (
    COMPETITOR_ANALYSIS_INSTRUCTION,
    COMPLETION_RULE_INSTRUCTION,
    DOMAIN_ADAPTATION_INSTRUCTION,
)


def seo_content_agent() -> Agent:
    """Create and return the Local SEO & Content Strategy Analyst agent"""
    return Agent(
        name="Local SEO & Content Strategy Analyst",
        role="Analyze local search presence, Google Maps optimization, and local content marketing for businesses.",
        model=agent_model(max_tokens=8000),
        tools=all_tools(),
        instructions=[
            "STEP 0 — TARGET COMPANY SELF-AUDIT (do this before analyzing competitors):",
            "  Search '{company} official website' → audit the target's own site quality",
            "  Search '{company} Google Business Profile {location}' → audit GBP completeness",
            "  Search '{company} Instagram {location}' → get follower count and post cadence",
            "  Search '{company} reviews Google {location}' → get own review count and rating",
            "  Present this as '### {company} — Self-Audit' section FIRST in your output",
            "",
            DOMAIN_ADAPTATION_INSTRUCTION,
            "",
            "Perform comprehensive local SEO and content analysis for {company} and competitors in {domain} in {location}. Adapt your analysis to the specific business type ({domain}).",
            "",
            COMPETITOR_ANALYSIS_INSTRUCTION,
            "In example search strings, «COMP» means substitute that competitor's exact business name.",
            "",
            "RESEARCH PROCESS FOR LOCAL BUSINESSES:",
            "  1. Search '«COMP» Google Maps listing {location}' → check local SEO presence",
            "  2. Search '«COMP» near me' → analyze local search rankings",
            "  3. Search '«COMP» reviews Google Yelp TripAdvisor' → check review platforms",
            "  4. Search '«COMP» social media Instagram Facebook' → assess social presence",
            "  5. Search 'best {domain} {location}' → see if competitor appears in top results",
            "  6. Search '«COMP» website content blog' → analyze content strategy",
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
            COMPLETION_RULE_INSTRUCTION,
            "- Ensure all analysis is complete before finishing each competitor section",
            "- You must complete your final sentence. Never end with a hyphen, an incomplete word, or a cut-off table cell. If you reach a length limit, finish the current sentence and stop.",
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
