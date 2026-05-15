#!/usr/bin/env python3
"""
Pricing & Business Model Analyst Agent
Simplified version - fixes empty output issue
"""

from agno.agent import Agent
from ..models import agent_model
from ..tools import all_tools


def pricing_business_agent() -> Agent:
    """Create and return the Pricing & Business Model Analyst agent"""
    return Agent(
        name="Universal Business Pricing & Strategy Analyst",
        role="Extract pricing information, business model, and competitive positioning.",
        model=agent_model(max_tokens=6000),
        tools=all_tools(),
        instructions=[
            "IMPORTANT: You MUST produce actual output. DO NOT return empty responses.",
            "",
            "TASK: Analyze pricing and business models for {company} and all competitors in {location}.",
            "Business type: {domain}",
            "",
            "OUTPUT FORMAT - USE THESE EXACT HEADERS:",
            "",
            "### {company} - Pricing & Business Model",
            "**Price Level:** [€/€€/€€€] | **Revenue Model:** [describe]",
            "",
            "**Menu/Basic Prices:**",
            "- [List key items with prices]",
            "",
            "**Business Model:**",
            "- [How they make money]",
            "",
            "---",
            "",
            "### [Competitor Name]",
            "**Price Level:** [€/€€/€€€] | **Revenue Model:** [describe]",
            "",
            "**Menu/Basic Prices:**",
            "- [List key items with prices]",
            "",
            "---",
            "",
            "REPEAT for EACH competitor from the provided list.",
            "",
            "SEARCH:",
            "1. Search '{company} menu prices {location}'",
            "2. Search 'best {domain} {location} prices'",
            "3. For each competitor: '[name] {domain} {location} prices'",
            "",
            "If no pricing found, state 'No data available' - never leave empty.",
            "",
            "MUST INCLUDE: Analyze at least 6 competitors plus {company}",
        ],
        markdown=True,
    )