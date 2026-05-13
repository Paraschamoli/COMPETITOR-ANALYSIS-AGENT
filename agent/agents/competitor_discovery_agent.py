#!/usr/bin/env python3
"""
Competitor Discovery Specialist Agent
Corrected version — fixes applied:
  1.  Template variables substituted via f-strings (function now accepts company/domain/location)
  2.  Duplicate DATA VERIFICATION RULES merged into one authoritative section
  3.  Contradictory 8 000-char limit removed; output completeness takes priority
  4.  Empty CATEGORIES TO IDENTIFY section removed
  5.  Min-6-competitor rule now has a clear priority chain over exclusion rules
  6.  Duplicate tool registration guarded with name-based deduplication
  7.  Scraper tool reference uses the actual registered tool name, not the hard-coded 'scrape'
  8.  Partial / wrong-location scraper results now have explicit fallback handling
  9.  Two conflicting field schemas consolidated into one canonical 7-column table
 10.  Instruction set trimmed from ~200 lines to ~80 — all duplication removed
 11.  Exact column headers and column order declared so main_modular.py parser is reliable
 12.  Prose formatting rules added to keep non-table sections short and parser-friendly
 13.  role field corrected to a noun phrase, not a behavioural description
"""

from agno.agent import Agent
from ..models import agent_model
from ..tools import all_tools, google_maps_scraper_tool
from ..config import GOOGLE_MAPS_SCRAPER_AVAILABLE


# ---------------------------------------------------------------------------
# Helper: resolve the name of any tool regardless of whether it is an Agno
# Tool object (has .name) or a plain Python function (has .__name__).
# ---------------------------------------------------------------------------
def _tool_name(tool) -> str:
    """Return the callable/tool name, handling both Agno objects and plain functions."""
    return (
        getattr(tool, "name", None)        # Agno Tool object  → .name
        or getattr(tool, "__name__", None)  # plain function    → .__name__
        or str(tool)                        # last-resort fallback
    )


def competitor_discovery_agent(company: str, domain: str, location: str) -> Agent:
    """
    Create and return the Competitor Discovery Specialist agent.

    Parameters
    ----------
    company  : Target business name, e.g. "Foodhallen"
    domain   : Business category,    e.g. "food hall"
    location : Geographic focus,     e.g. "Amsterdam"
    """

    # ------------------------------------------------------------------
    # Tool list — deduplicated so the scraper is never registered twice.
    # Works whether tools are Agno objects or plain functions (fix #6).
    # ------------------------------------------------------------------
    tools = all_tools()
    if GOOGLE_MAPS_SCRAPER_AVAILABLE:
        maps_tool = google_maps_scraper_tool()
        existing_names = {_tool_name(t) for t in tools}
        if _tool_name(maps_tool) not in existing_names:
            tools.append(maps_tool)

    # Capture the exact tool name for use in instructions (fix #7).
    maps_tool_name = _tool_name(google_maps_scraper_tool()) if GOOGLE_MAPS_SCRAPER_AVAILABLE else None

    # ------------------------------------------------------------------
    # Build instructions with all variables substituted (fix #1).
    # Every {company}, {domain}, {location} becomes a real value here.
    # ------------------------------------------------------------------
    scraper_block = (
        [
            "═══ STEP 1 — GOOGLE MAPS SCRAPER (primary source) ═══",
            f"Call the '{maps_tool_name}' tool with query='{domain}' and location='{location}'.",
            "The scraper returns JSON with: name, address, rating, review_count, price_level, hours, website.",
            "Use those values as the single source of truth for Rating and Review Count.",
            "",
            "Scraper fallback — trigger ANY of these conditions:",
            "  • Tool call returns an error or times out",
            "  • Returned JSON is empty or unparseable",
            "  • Fewer than 6 results in the response",
            "  • Any result has an address outside of " + location,
            "When fallback triggers, supplement (do not abandon scraper data already obtained) with:",
            f"  1. Search '{domain} near {location}'",
            f"  2. Search 'best {domain} in {location}'",
            f"  3. Search 'top rated {domain} {location} reviews'",
        ]
        if GOOGLE_MAPS_SCRAPER_AVAILABLE
        else [
            "═══ STEP 1 — WEB SEARCH (Google Maps scraper not enabled) ═══",
            f"Execute these searches in order to discover competitors:",
            f"  1. Search '{domain} near {location}'",
            f"  2. Search 'best {domain} in {location}'",
            f"  3. Search 'top rated {domain} {location} reviews'",
        ]
    )

    instructions = [
        # ── ROLE & OBJECTIVE ──────────────────────────────────────────
        f"You are a Local Business Competitor Discovery Specialist.",
        f"Your task: discover and profile the top competitors for '{company}' "
        f"in the '{domain}' category in {location}.",
        "CRITICAL: Use real tool calls for every data point. "
        "Never invent, estimate, or hallucinate business information.",
        "",

        # ── SEARCH PROCESS ────────────────────────────────────────────
        *scraper_block,
        "",
        "═══ STEP 2 — FILL DATA GAPS ═══",
        f"For each competitor found, if address or rating is missing:",
        f"  • Search '<competitor name> {location} address'",
        f"  • Search '<competitor name> {location} Google Maps rating'",
        "",

        # ── COMPETITOR SELECTION RULES ────────────────────────────────
        "═══ COMPETITOR SELECTION RULES ═══",
        f"INCLUDE: businesses that offer the same or similar services as '{company}' "
        f"and are physically located in {location}.",
        f"EXCLUDE: vendors operating inside '{company}', businesses in a different city, "
        "businesses in an unrelated category.",
        "",
        "MINIMUM / REVIEW-COUNT PRIORITY CHAIN (fix for conflicting rules):",
        "  Tier 1 — prefer competitors with ≥ 100 reviews and a complete profile.",
        "  Tier 2 — if Tier 1 yields < 6 competitors, include competitors with 50–99 reviews; "
        "           mark their Review Count cell as '⚠ Limited sample'.",
        "  Tier 3 — if Tier 1+2 still yields < 6, include the best available competitors "
        "           regardless of review count; mark as '⚠ Low data'.",
        "  NEVER fabricate a competitor to reach 6. If only N real competitors exist, report N.",
        "  AIM for 6–10 competitors total.",
        "",

        # ── DATA VERIFICATION (single, authoritative block) ───────────
        "═══ DATA VERIFICATION ═══",
        "For every data point, record its source as one of:",
        "  Verified-Scraper  →  came directly from the Maps scraper JSON",
        "  Verified-Search   →  confirmed via a web search result",
        "  Unavailable       →  not found after ≥ 2 search attempts",
        "Never leave the Verification cell blank.",
        "If two sources disagree on Rating or Review Count, prefer Verified-Scraper; "
        "note the discrepancy in parentheses, e.g. '4.3 (Yelp: 4.1)'.",
        "Use the same Rating and Review Count for a given business in every section "
        "of your output — no inconsistencies.",
        "",

        # ── CANONICAL OUTPUT SCHEMA ───────────────────────────────────
        "═══ REQUIRED OUTPUT — SECTION 1: DISCOVERY TABLE ═══",
        "Output a markdown table with EXACTLY these column headers in this order "
        "(main_modular.py parses this table by these exact names):",
        "",
        "| Name | Address | Rating | Review Count | Price Range | Specialties | Verification |",
        "|------|---------|--------|--------------|-------------|-------------|--------------|",
        "",
        "Rules:",
        "  • 'Name'         — exact trading name, no abbreviations",
        "  • 'Address'      — street + city; use '—' only if genuinely not found",
        "  • 'Rating'       — e.g. 4.3/5; use '—' if unavailable",
        "  • 'Review Count' — integer or '—'; append ⚠ flag from selection rules above if needed",
        "  • 'Price Range'  — $, $$, $$$, or $$$$",
        "  • 'Specialties'  — ≤ 10 words; most distinctive offering",
        "  • 'Verification' — one of the three statuses defined above",
        "  • Never leave a cell blank — use '—' as the empty sentinel",
        "  • Never cut a row mid-cell",
        f"  • Include '{company}' as the FIRST row, labelled as the target business",
        "",

        # ── REQUIRED OUTPUT — COMPARISON MATRIX ──────────────────────
        "═══ REQUIRED OUTPUT — SECTION 2: COMPARISON MATRIX ═══",
        "After the discovery table, output a second markdown table:",
        "",
        "| Name | Rating | Review Count | Price Range | Hours | Website |",
        "|------|--------|--------------|-------------|-------|---------|",
        "",
        "Use the same Name and numeric values from Section 1 — no new numbers.",
        "",

        # ── REQUIRED OUTPUT — COMPETITIVE LANDSCAPE SUMMARY ──────────
        "═══ REQUIRED OUTPUT — SECTION 3: COMPETITIVE LANDSCAPE SUMMARY ═══",
        "After the two tables, write a brief landscape summary.",
        "Format: one short paragraph (3–5 sentences) covering market structure, "
        "dominant players, and any notable gaps.",
        "Then list each competitor as a single line:",
        "  **<Name>** — <location area>, <key differentiator>, targets <audience>.",
        "Do not repeat rating/review numbers already in the tables.",
        "",

        # ── FORMATTING RULES ─────────────────────────────────────────
        "═══ FORMATTING RULES ═══",
        "Use ## for section headers (Section 1, 2, 3 above).",
        "Do not use nested bullet lists inside table cells.",
        "Do not bold individual words inside prose — bold only competitor names in the landscape list.",
        "Complete every sentence. Never end output with a hyphen, partial word, or open table row.",
        "If you are approaching your output limit, finish the current row or sentence, "
        "then stop — do not truncate mid-cell.",
    ]

    return Agent(
        name="Local Business Competitor Discovery Specialist",
        # role is a noun phrase for orchestration routing, not a behavioural description (fix #13)
        role="Competitor Discovery Specialist",
        model=agent_model(),
        tools=tools,
        instructions=instructions,
        markdown=True,
    )