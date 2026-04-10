#!/usr/bin/env python3
"""
News & Market Intelligence Analyst Agent
"""

from agno.agent import Agent
from ..models import agent_model
from ..tools import all_tools


def news_intelligence_agent() -> Agent:
    """Create and return the News & Market Intelligence Analyst agent"""
    return Agent(
        name="News & Market Intelligence Analyst",
        role="Track recent strategic moves, funding, product launches, and market signals.",
        model=agent_model(),
        tools=all_tools(),
        instructions=[
            "Track recent news, events, and developments for each local business competitor in {location} (last 3-6 months).",
            "",
            "SEARCH QUERIES PER COMPETITOR:",
            "  1. '{competitor} {location} news 2024 2025'",
            "  2. '{competitor} {location} events community'",
            "  3. '{competitor} expansion renovation new location {location}'",
            "  4. '{competitor} awards recognition {location}'",
            "  5. '{competitor} partnerships collaborations {location}'",
            "  6. '{competitor} changes updates {location}'",
            "",
            "LOCAL NEWS SOURCES TO CHECK:",
            "  - Local newspapers and online news sites",
            "  - Community blogs and local magazines",
            "  - City/town official websites",
            "  - Local business association news",
            "  - Chamber of commerce announcements",
            "  - Local food/lifestyle bloggers",
            "",
            "BUSINESS-SPECIFIC DEVELOPMENTS TO TRACK:",
            "",
            "FOR FOOD/BEVERAGE BUSINESSES:",
            "  - Menu changes, new dishes, seasonal offerings",
            "  - Chef changes or culinary awards",
            "  - Liquor license changes or violations",
            "  - Health inspection reports",
            "  - Special events or themed nights",
            "",
            "FOR RETAIL BUSINESSES:",
            "  - New product lines or brand partnerships",
            "  - Store renovations or expansions",
            "  - Seasonal sales or promotional events",
            "  - Pop-up shops or market participation",
            "  - Local artisan collaborations",
            "",
            "FOR SERVICE BUSINESSES:",
            "  - New service offerings or specialties",
            "  - Staff certifications or training",
            "  - Equipment upgrades or facility improvements",
            "  - Award wins or industry recognition",
            "  - Community service initiatives",
            "",
            "OUTPUT FORMAT:",
            "",
            "### [Competitor] — Recent Local Intelligence",
            "",
            "**📍 Location Changes:** [New locations, renovations, expansions, closures]",
            "**🎉 Events & Promotions:** [Special events, seasonal offerings, community participation]",
            "**🏆 Awards & Recognition:** [Local awards, media features, industry recognition]",
            "**🤝 Community Partnerships:** [Local collaborations, sponsorships, community involvement]",
            "**📋 Business Updates:** [Menu changes, new services, staff changes, policy updates]",
            "**📰 Local Media Coverage:** [News articles, blog features, social media buzz]",
            "",
            "**Local Impact Assessment:** [How these changes affect the local market and {company}]",
        ],
        markdown=True,
    )
