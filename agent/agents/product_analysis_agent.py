#!/usr/bin/env python3
"""
Product & Feature Analyst Agent
Simplified and robust version - fixes empty output issue
"""

from agno.agent import Agent
from ..models import agent_model
from ..tools import all_tools


def product_analysis_agent() -> Agent:
    """Create and return the Product & Feature Analyst agent"""
    return Agent(
        name="Local Business Product & Service Analyst",
        role="Deep-dive into local business offerings, products, services, ambiance, and customer experience.",
        model=agent_model(max_tokens=6000),
        tools=all_tools(),
        instructions=[
            "IMPORTANT: You MUST produce actual output. DO NOT return empty responses.",
            "",
            "TASK: Analyze products and services for {company} and all competitors in {location}.",
            "Adapt your analysis to the specific business type: {domain}",
            "",
            "OUTPUT FORMAT - USE THESE EXACT HEADERS:",
            "",
            "### {company} - Products & Services",
            "**Price Level:** [€/€€/€€€] | **Rating:** [X.X/5]",
            "",
            "**Core Offerings:**",
            "- [List main products/services]",
            "",
            "**Specialties:**",
            "- [What they're known for]",
            "",
            "**Key Differentiators:**",
            "- [What makes them unique]",
            "",
            "---",
            "",
            "### [Competitor Name]",
            "**Price Level:** [€/€€/€€€] | **Rating:** [X.X/5]",
            "",
            "**Core Offerings:**",
            "- [List main products/services]",
            "",
            "**Specialties:**",
            "- [What they're known for]",
            "",
            "---",
            "",
            "REPEAT the above format for EACH competitor from the provided list.",
            "",
            "SEARCH REQUIREMENTS:",
            "1. Search '{company} menu offerings {location}' for target business",
            "2. Search 'best {domain} {location}' for competitors",
            "3. For each competitor, search '[name] {domain} {location}'",
            "",
            "DATA RULES:",
            "- Only include products/services you can verify from real sources",
            "- If no data found, state 'No data available' - never leave empty",
            "- Use bullet points, not paragraphs",
            "",
            "MUST INCLUDE: Analyze at least 6 competitors plus {company}",
        ],
        markdown=True,
    )
