"""
Seeded demo data for DEMO_MODE.

24-month window (Jul 2024 -> Jun 2026), oldest -> newest.
Designed to produce a realistic but illustrative velocity pattern:
  BIS   -> SURGE    (z ~ 6.4) -- semiconductor/AI export rule explosion
  CMMC  -> SURGE    (z ~ 3.7) -- CMMC 2.0 final rule implementation cascade
  DFARS -> ELEVATED (z ~ 1.5) -- CMMC-linked DFARS interim rules
  ITAR  -> NORMAL   (z ~ 0.9) -- routine annual updates
  SEAD  -> QUIET    (z ~ -2.1) -- post-NISPOM consolidation pause
"""

# Monthly Federal Register publication counts per domain (24 months)
DEMO_TIMESERIES: dict[str, list[int]] = {
    "DFARS": [14, 10, 15, 11, 16, 10, 14, 11,  9, 15, 13, 10,
              12, 16,  9, 14, 11, 16,  9, 14, 15, 16, 17, 15],
    "CMMC":  [ 3,  4,  3,  5,  3,  4,  5,  3,  4,  5,  4,  5,
               4,  5,  4,  6,  5,  4,  6,  5,  6,  8,  9,  8],
    "ITAR":  [ 6,  7,  5,  6,  8,  6,  7,  5,  6,  7,  6,  5,
               7,  6,  5,  7,  6,  7,  6,  5,  7,  7,  6,  8],
    "BIS":   [ 7,  9,  6,  8, 10,  7,  9,  8,  6, 11,  7,  8,
               9,  5, 10,  8,  9, 11,  7,  8,  6, 17, 20, 19],
    "SEAD":  [ 3,  2,  3,  3,  4,  3,  2,  3,  4,  2,  3,  3,
               4,  2,  3,  3,  4,  2,  3,  3,  4,  2,  1,  2],
}

DEMO_BRIEFS: dict[str, str] = {
    "BIS": (
        "BIS export control rulemaking has surged to more than 3x historical baseline over "
        "the past quarter. The acceleration tracks directly with the 2026 semiconductor and "
        "advanced AI export control regime: three major Entity List additions targeting "
        "Chinese chip fabrication equipment suppliers (March 2026), two Emergency Industry "
        "and Security rules addressing high-bandwidth memory chip exports (April 2026), and "
        "the final rule implementing Diffusion Rule controls on AI model weights and frontier "
        "model deployment (June 2026). Defense contractors with dual-use technology supply "
        "chains should anticipate continued elevated rule velocity through 2026 as BIS "
        "completes the enforcement framework supporting the CHIPS and Science Act."
    ),
    "CMMC": (
        "CMMC publication rate has increased 47% over the prior quarter, reflecting the full "
        "implementation phase of CMMC 2.0. The March 2026 final rule codifying Level 2 "
        "third-party assessment requirements for all DoD contracts exceeding $3M triggered a "
        "cascade of DFARS interim rules and clarifying notices. Defense Industrial Base "
        "contractors not yet certified at CMMC Level 2 face an accelerating compliance "
        "deadline as DoD CIO integrates assessment clauses across acquisition programs. "
        "Organizations should treat the current surge as a preparation window, not a warning "
        "of further rule changes -- the framework is now largely set."
    ),
    "DFARS": (
        "DFARS rule velocity is elevated at approximately 1.5 standard deviations above "
        "baseline. The primary driver is CMMC 2.0 assessment requirement implementation via "
        "DFARS subpart 204.21 revisions and supplementary interim rules. Secondary "
        "contributors include updated Specialty Metals domestic sourcing requirements under "
        "10 U.S.C. 4863 and Section 889 telecommunications prohibition updates following "
        "FCC rulemaking. The elevated rate indicates continued moderate pressure through "
        "Q3 2026 but does not represent a structural shift in DFARS publication cadence."
    ),
    "ITAR": (
        "ITAR publication activity remains within normal historical range with a modest "
        "17% quarter-over-quarter uptick. The slight increase reflects routine annual updates "
        "to USML Category I (firearms) and Category VI (aircraft and spacecraft) following "
        "the State Department's standard review cycle, plus one proposed rule addressing "
        "commercial satellite technology classification thresholds. No major structural "
        "amendments to the ITAR framework are currently in progress, though the pending "
        "modernization of Category XX (nuclear) remains a potential velocity driver if "
        "progressed to proposed rulemaking in late 2026."
    ),
    "SEAD": (
        "Security and personnel security directive publications are in a quiet period, "
        "running approximately 50% below prior-period levels and well below historical "
        "baseline. This follows the completion of the NISPOM Rule (32 CFR Part 117) "
        "implementation cycle in 2025 and reflects a post-rulemaking consolidation phase "
        "in which DoD Security is primarily issuing guidance documents rather than formal "
        "rules. The Personnel Security Research Center's pending review of adjudicative "
        "guidelines may produce a new proposed rule in late 2026, which would reverse the "
        "current quiet trend."
    ),
    "_system": (
        "The defense regulatory environment as of Q2 2026 shows a bifurcated velocity "
        "pattern. BIS export controls and CMMC cybersecurity compliance are in surge -- both "
        "running significantly above historical baseline -- driven by the convergence of the "
        "2026 semiconductor/AI export restriction regime and CMMC 2.0 final implementation. "
        "DFARS is elevated as it absorbs CMMC-linked rulemaking. ITAR and SEAD are normal "
        "to quiet, providing a counterweight to the surge domains. For defense contractors, "
        "this pattern represents the most compressed dual compliance timeline in the past "
        "decade: organizations must simultaneously absorb new export control obligations "
        "and achieve CMMC certification while DFARS clauses are actively being revised. "
        "Prioritize export control counsel review and CMMC assessment scheduling in Q3 2026."
    ),
}
