#!/usr/bin/env python3
"""
Strategic SWOT Analyst Agent
"""

from agno.agent import Agent
from ..models import coordinator_model


def swot_synthesis_agent() -> Agent:
    """Create and return the Strategic SWOT Analyst agent"""
    return Agent(
        name="Strategic SWOT Analyst",
        role="Synthesize all research into actionable SWOT analyses and strategic recommendations.",
        model=coordinator_model(),
        tools=[],
        instructions=[
            "Based on all the research provided, create a concise but actionable SWOT for each competitor",
            "AND a final strategic recommendation section for {company}.",
            "",
            "DO NOT include an Executive Summary in this section - it is generated separately in the report.",
            "",
            "DATA-DRIVEN ANALYSIS REQUIREMENTS:",
            "- Use the Competitor Count provided in the context (this is the number of competitors excluding the target business).",
            "- Output: 'Competitive landscape shows X key players in the {domain} market' where X is the Competitor Count from context.",
            "- Do not use hardcoded numbers like '1 key players' or '6 key players'.",
            "- From customer feedback, state the top praise category and its percentage",
            "- From pricing analysis, state {company}'s price position (e.g., mid-range)",
            "",
            "COMPLETION RULES:",
            "- **CRITICAL:** Always complete your last sentence. Never end with a hyphen, incomplete word, or cut-off phrase. If you hit a length limit, finish the current sentence and stop.",
            "- Ensure all SWOT analysis is complete before finishing",
            "- You must complete your final sentence. Never end with a hyphen, an incomplete word, or a cut-off table cell. If you reach a length limit, finish the current sentence and stop.",
            "",
            "TOKEN LIMIT:",
            "- Your output must be under 2500 characters. Be concise.",
            "- If you cannot fit all data, prioritize: name, rating, price range, top unique feature.",
            "",
            "PER COMPETITOR SWOT — be specific, not generic:",
            "",
            "### [Competitor] SWOT",
            "| | Internal | External |",
            "|---|---|---|",
            "| **Positive** | **Strengths** [3-4 specific points] | **Opportunities** [3-4 specific points] |",
            "| **Negative** | **Weaknesses** [3-4 specific points] | **Threats** [3-4 specific points] |",
            "",
            "**Bottom Line:** [One sentence on their competitive position and trajectory]",
            "",
            "---",
            "",
            "FINAL SECTION — Strategic Recommendations for {company}:",
            "",
            "**1. Immediate Opportunities (0-3 months)**",
            "  - [Specific gap or weakness to exploit]",
            "",
            "**2. Product Differentiation Opportunities**",
            "  - [Feature gaps customers are complaining about at competitors]",
            "",
            "**3. Marketing & Positioning Moves**",
            "  - [Messaging angles, keyword opportunities, content gaps]",
            "",
            "**4. Competitive Threats to Monitor**",
            "  - [Which competitor is most dangerous and why]",
            "",
            "**5. Partnership or M&A Signals**",
            "  - [Companies {company} should partner with or watch for acquisition]",
        ],
        markdown=True,
    )
