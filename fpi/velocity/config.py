"""Regulatory Velocity Tracker configuration."""
import os
from dotenv import load_dotenv

from fpi.shared import is_demo_mode

load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
DEMO_MODE: bool = is_demo_mode()  # shared permissive convention
MODEL: str = os.getenv("REGVEL_MODEL", "claude-haiku-4-5-20251001")

FR_BASE = "https://www.federalregister.gov/api/v1/documents.json"
USER_AGENT = "RegulatoryVelocity/1.0 (portfolio; contact jak.potvin@gmail.com)"
FR_TIMEOUT = 10       # seconds per API request
FR_RATE_LIMIT = 0.25  # seconds between successive API calls

# Federal Register `conditions[type]` filter expects the API's own enum CODES,
# not the human-readable labels the API returns in each document's `type` field.
# Passing a label like "Proposed Rule" is not an error -- the API returns HTTP
# 200 with count=0, silently matching nothing. Every DOMAINS[...]["doc_types"]
# label below must map to a code here. (Verified live 2026-07-07: BIS June 2026
# returns 90 with RULE/PRORULE/NOTICE vs. 0 with the labels.)
FR_TYPE_CODES: dict[str, str] = {
    "Rule": "RULE",                # Final Rule
    "Proposed Rule": "PRORULE",
    "Notice": "NOTICE",
    "Presidential Document": "PRESDOCU",
}

# History window for velocity analysis
HISTORY_MONTHS: int = 24
# Months considered "recent" for current velocity (trailing window)
RECENT_MONTHS: int = 3
# Minimum months of baseline required before z-score is meaningful
MIN_BASELINE_MONTHS: int = 6

# Z-score thresholds for velocity alert levels
ALERT_THRESHOLDS: dict[str, float] = {
    "SURGE":    2.0,
    "ELEVATED": 1.0,
    "QUIET":   -1.0,  # below this threshold → QUIET
}

ALERT_COLORS: dict[str, str] = {
    "SURGE":             "bold red",
    "ELEVATED":          "yellow",
    "NORMAL":            "green",
    "QUIET":             "dim",
    "INSUFFICIENT_DATA": "dim",
}

# Defense-relevant regulatory domains tracked by the Federal Register
DOMAINS: dict[str, dict] = {
    "DFARS": {
        "name": "Defense Federal Acquisition Regulation Supplement",
        "search_term": "DFARS",
        "doc_types": ["Rule", "Proposed Rule", "Notice"],
        "context": "DoD procurement, contracting, and acquisition rules",
    },
    "CMMC": {
        "name": "Cybersecurity Maturity Model Certification",
        "search_term": "Cybersecurity Maturity Model Certification",
        "doc_types": ["Rule", "Proposed Rule"],
        "context": "DoD cybersecurity compliance requirements for defense contractors",
    },
    "ITAR": {
        "name": "International Traffic in Arms Regulations",
        "search_term": "International Traffic in Arms",
        "doc_types": ["Rule", "Proposed Rule", "Notice"],
        "context": "US munitions and defense technology export controls",
    },
    "BIS": {
        "name": "Bureau of Industry and Security Export Controls",
        "search_term": "Export Administration Regulations",
        "doc_types": ["Rule", "Proposed Rule", "Notice"],
        "context": "Dual-use technology, semiconductor, and AI export restrictions",
    },
    "SEAD": {
        "name": "Security / Personnel Security Directives",
        "search_term": "NISPOM personnel security",
        "doc_types": ["Rule", "Notice"],
        "context": "Industrial security, clearance adjudications, NISPOM requirements",
    },
}
