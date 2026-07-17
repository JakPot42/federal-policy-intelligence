# Federal Policy Intelligence (`fpi`)

A unified command-line toolkit for **federal regulatory and policy analysis**,
combining three tools into one CLI on a shared core.

```
fpi comments   Rulemaking Comment Analyzer   -- Regulations.gov public comments
fpi policy     AI Policy Impact Simulator     -- cited-corpus stakeholder simulation
fpi velocity   Regulatory Velocity Tracker    -- Federal Register rate-of-change
fpi demo       Run all three tool demos end to end (no API keys required)
```

All three default to `DEMO_MODE=True` and run fully offline with no API keys.
Set `DEMO_MODE=False` (and provide keys) for live data.

## The three tools

### `fpi comments` -- Rulemaking Comment Analyzer
Ingests public comments for a Regulations.gov docket, classifies each by theme,
stakeholder type, and stance (Claude extracts; deterministic logic clusters),
and generates a structured government decision memorandum.

```
fpi comments demo                              # seeded CMMC 2.0 docket, no keys
fpi comments analyze DoD-2023-OS-0063
fpi comments browse DoD-2023-OS-0063 --stance OPPOSE --stakeholder INDUSTRY
fpi comments memo DoD-2023-OS-0063
```

### `fpi policy` -- AI Policy Impact Simulator
Paste draft AI policy language; four stakeholder personas react, unintended
consequences are flagged, and the draft is scored against NIST AI RMF and the
EU AI Act -- **every citation verified against a real indexed corpus** (NIST AI
RMF 1.0, DoD AI Ethical Principles, EU AI Act Articles 5/6, EO 14179, EO 14365)
before it is shown as confirmed.

```
fpi policy demo                                # two contrasting example drafts
fpi policy analyze --file draft.txt
fpi policy search "facial recognition"
fpi policy corpus                              # list everything it can cite
```

### `fpi velocity` -- Regulatory Velocity Tracker
Measures how fast defense regulations are changing -- publication rate vs. a
rolling baseline (z-score) per domain (DFARS, CMMC, ITAR, BIS, SEAD) from the
Federal Register API.

```
fpi velocity demo
fpi velocity compare
fpi velocity series BIS
fpi velocity brief CMMC
```

## Architecture: the shared core

`fpi/shared/` holds the two things all three tools genuinely share:

- **`demo_mode.py`** -- one `is_demo_mode()`, the permissive convention
  (`DEMO_MODE` off only for `false`/`0`/`no`). This reconciles the AI Policy
  Simulator's original strict `== "True"` parse into the convention the other
  two already used.
- **`claude_client.py`** -- one `call_claude(..., on_error="raise"|"fallback")`.
  The Comment Analyzer and Velocity Tracker raise loudly on a Claude failure;
  the Policy Simulator falls back to a deterministic template. Both behaviors
  are first-class via the `on_error` parameter -- no call site has to guess.
  Catches broad `Exception` (the SDK raises `TypeError`, not `APIError`, on a
  missing key).

Each tool's domain logic (`fpi/comments/`, `fpi/policy/`, `fpi/velocity/`) is
ported unchanged onto that core. Note: the Policy Simulator's BM25 index is
**not** in the shared core -- it is the only tool that uses retrieval, so it
stays local to `fpi/policy/`.

## Install / run

```
pip install -e .          # provides the `fpi` command
# or, without installing:
python main.py comments demo
```

## Tests

```
pytest
```

332 tests: 24 shared-core + 131 comments + 69 policy + 108 velocity. Output is
verified ASCII-safe under strict encoding (no Unicode that would crash a Windows
OEM console).

## Provenance

Merges `JakPot42/comment-analyzer`, `JakPot42/ai-policy-simulator`,
and `JakPot42/regulatory-velocity`. All three remain independent,
separately-runnable standalone repos; this toolkit adds a unified CLI on top.
