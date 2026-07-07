"""
Federal Register API client.

Live mode: queries federalregister.gov for monthly publication counts per domain.
DEMO_MODE: returns seeded data from seed_data.py — no HTTP calls.

API reference: https://www.federalregister.gov/reader-aids/developer-resources/rest-api
"""
from __future__ import annotations

import calendar
import time
from datetime import date

import requests

from .config import (
    DEMO_MODE,
    DOMAINS,
    FR_BASE,
    FR_RATE_LIMIT,
    FR_TIMEOUT,
    FR_TYPE_CODES,
    HISTORY_MONTHS,
    USER_AGENT,
)
from .velocity_engine import _month_labels


def type_codes(doc_types: list[str]) -> list[str]:
    """Translate human-readable document-type labels into the Federal Register
    API's `conditions[type]` enum codes. An unknown label raises rather than
    silently producing a filter the API answers with count=0 (see Bug B note in
    _fetch_live). Pure function, unit-tested without network access."""
    codes: list[str] = []
    for label in doc_types:
        if label not in FR_TYPE_CODES:
            raise ValueError(
                f"Unknown Federal Register document type {label!r}; "
                f"add it to config.FR_TYPE_CODES."
            )
        codes.append(FR_TYPE_CODES[label])
    return codes


def fetch_domain_counts(
    domain_key: str,
    months_back: int = HISTORY_MONTHS,
    *,
    demo_mode: bool = DEMO_MODE,
) -> tuple[list[str], list[int | None]]:
    """
    Return (months, counts) for the past months_back months.

    months: ["2024-07", ..., "2026-06"] oldest first
    counts: monthly Federal Register publication count for this domain. A count
        is an int (including a genuine 0 -- a month the API confirmed had no
        matching documents) OR None, meaning the fetch for that month FAILED and
        the value is unknown. None is deliberately distinct from 0 so a network/
        HTTP failure is never silently counted as a real quiet month in the
        z-score baseline (see velocity_engine.build_series, which drops None).
    """
    labels = _month_labels(months_back)

    if demo_mode:
        from .seed_data import DEMO_TIMESERIES
        raw = DEMO_TIMESERIES.get(domain_key, [])
        # If seed data is shorter than requested window, left-pad with zeros
        if len(raw) < months_back:
            raw = [0] * (months_back - len(raw)) + list(raw)
        return labels, list(raw[-months_back:])

    return _fetch_live(domain_key, labels)


def _fetch_live(domain_key: str, labels: list[str]) -> tuple[list[str], list[int | None]]:
    domain_cfg = DOMAINS[domain_key]
    counts: list[int | None] = []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    for label in labels:
        year, month = int(label[:4]), int(label[5:7])
        last_day = calendar.monthrange(year, month)[1]
        params: dict = {
            "conditions[term]": domain_cfg["search_term"],
            "conditions[publication_date][gte]": f"{year}-{month:02d}-01",
            "conditions[publication_date][lte]": f"{year}-{month:02d}-{last_day:02d}",
            "per_page": 1,
            "page": 1,
            "fields[]": "publication_date",
            # Bug B fix: send the API's enum CODES (RULE/PRORULE/NOTICE), not the
            # human-readable labels. Labels are not rejected -- they return HTTP
            # 200 with count=0 -- so the whole live path used to read as an empty
            # regulatory record for every domain.
            "conditions[type][]": type_codes(domain_cfg["doc_types"]),
        }

        try:
            resp = session.get(FR_BASE, params=params, timeout=FR_TIMEOUT)
            resp.raise_for_status()
            counts.append(int(resp.json().get("count", 0)))
        except Exception:
            # Bug A fix: a failed fetch is UNKNOWN, not zero. Recording 0 here
            # would let a transient network/HTTP error masquerade as a genuine
            # quiet month and distort the very baseline this tool computes.
            counts.append(None)

        time.sleep(FR_RATE_LIMIT)

    return labels, counts


def fetch_all_domains(
    domains: list[str] | None = None,
    months_back: int = HISTORY_MONTHS,
    *,
    demo_mode: bool = DEMO_MODE,
) -> dict[str, tuple[list[str], list[int | None]]]:
    """
    Fetch counts for all (or specified) domains.

    Returns {domain_key: (months, counts)}.
    """
    keys = domains if domains is not None else list(DOMAINS.keys())
    return {
        key: fetch_domain_counts(key, months_back, demo_mode=demo_mode)
        for key in keys
    }
