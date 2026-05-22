#!/usr/bin/env python3
"""
Shared instruction constants for agent prompts.
Reduces duplication across agent files and makes updates easier.
"""

# Common critical instructions
COMPETITOR_ANALYSIS_INSTRUCTION = (
    "CRITICAL: You MUST analyze EVERY competitor from the provided competitor list. "
    "Loop through each competitor. Do not skip any. If a competitor has no data, "
    "mark 'No data available' and continue."
)

COMPLETION_RULE_INSTRUCTION = (
    "CRITICAL: Always complete your last sentence. Never end with a hyphen, incomplete word, "
    "or cut-off phrase. If you hit a length limit, finish the current sentence and stop."
)

VERIFICATION_INSTRUCTION = (
    "CRITICAL: You MUST perform actual web searches and verify all data. "
    "DO NOT hallucinate products, services, or business details. "
    "Only include information you can verify from real sources (websites, catalogs, service listings, reviews)."
)

DOMAIN_ADAPTATION_INSTRUCTION = (
    "Before analyzing, check {domain} parameter. Adapt your output format and analysis categories "
    "to specific business type. Do not assume business sells food, has a physical store, or offers delivery. "
    "Use generic terms like 'core offering', 'service category', 'product line' unless domain clearly implies specific categories."
)

# Combined instruction sets for common use cases
STANDARD_ANALYSIS_INSTRUCTIONS = [
    COMPETITOR_ANALYSIS_INSTRUCTION,
    "In example search strings, «COMP» means substitute that competitor's exact business name.",
]

STANDARD_COMPLETION_INSTRUCTIONS = [
    COMPLETION_RULE_INSTRUCTION,
    "Ensure all analysis is complete before finishing each section",
    "You must complete your final sentence. Never end with a hyphen, an incomplete word, or cut-off table cell. "
    "If you reach a length limit, finish the current sentence and stop.",
]
