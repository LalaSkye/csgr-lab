![CI](https://github.com/LalaSkye/csgr-lab/actions/workflows/ci.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)

# csgr-lab

Contracted stability and drift measurement for LLM behaviour — deterministic scoring, hash-chained evidence, reproducible runs.

**v0.1.0** | MIT License

---

## Why This Exists

You cannot govern what you cannot measure. Most LLM evaluation tools focus on quality metrics — helpfulness, coherence, preference. This tool focuses on contract conformance: did the system do what it was specified to do, and can you prove it? Every scoring run produces immutable, hash-chained evidence. Same inputs always produce the same scores. `csgr-lab` is the measurement layer that feeds into the governance architecture: execution gates and commit boundaries can only enforce contracts that have been scored and logged.

---

## Architecture

```
ContractSpec + Measurements
        |
        v
  ScoringEngine.score()
        |
        v
  ScoringRun (immutable)
        |
        +---> EvidenceLogger.log()     ---> JSONL with SHA-256 hash chain
        |
        +---> DriftDetector.analyze()  ---> DriftReport (z-score vs baseline)
```

---

## Quickstart

```bash
git clone https://github.com/LalaSkye/csgr-lab.git
cd csgr-lab
pip install .

# Score a contract against measurements
csgr score contract.json measurements.json

# Verify evidence chain integrity
csgr verify

# Show version
csgr version
```

Expected output from `csgr score`:

```
Scoring run: abc12345
  contract  : contract.json
  clauses   : 4
  score     : 0.8750
  drift     : NONE (no baseline)
  evidence  : evidence.jsonl (hash: sha256:e3b0c44...)
```

Expected output from `csgr verify` (clean chain):

```
Verifying evidence chain...
  records  : 12
  chain    : VALID
  result   : OK
```

Expected output from `csgr verify` (tampered chain):

```
Verifying evidence chain...
  records  : 12
  chain    : INVALID at record 7
  result   : FAIL
```

---

## Module Structure

| Module | Purpose |
|---|---|
| `contracts/` | Pydantic frozen models defining behavioural expectations (`ClauseSpec`, `ContractSpec`) |
| `scoring/` | Deterministic scoring engine producing immutable `ScoringRun` records |
| `evidence/` | Append-only JSONL logger with SHA-256 hash chain for tamper-evident audit |
| `drift/` | Z-score analysis for detecting regression or improvement against baselines |
| `config/` | Pydantic-settings configuration with `CSGR_` environment variable prefix |

---

## Contract Format

A `ContractSpec` is a JSON file defining one or more `ClauseSpec` entries. Each clause specifies what is being measured, the expected range, and how to score it.

```json
{
  "contract_id": "example-v1",
  "clauses": [
    {
      "clause_id": "latency",
      "description": "p99 latency under 500ms",
      "metric": "latency_p99_ms",
      "threshold": 500,
      "operator": "lte"
    },
    {
      "clause_id": "refusal_rate",
      "description": "refusal rate below 5%",
      "metric": "refusal_rate_pct",
      "threshold": 5.0,
      "operator": "lte"
    }
  ]
}
```

---

## Design Constraints

- **Deterministic:** same inputs produce same outputs, verified by `verify_determinism()`
- **Immutable:** all records and results are frozen after creation
- **Auditable:** every run generates chained evidence with SHA-256 hashes
- **Fail-closed:** missing or malformed inputs produce errors, not defaults
- **Minimal:** core logic uses stdlib + Pydantic only

---

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## Relationship to Other Repositories

`csgr-lab` sits at the audit and evidence layer of the control stack. It consumes outputs from systems governed by execution gates and commit boundaries (see [constraint-workshop](https://github.com/LalaSkye/constraint-workshop)), and produces the tamper-evident evidence trail that proves contract conformance. The drift detection output surfaces whether behaviour has changed between versions — information that feeds back into [invariant-lock](https://github.com/LalaSkye/invariant-lock) enforcement decisions.

---

## Part of the Execution Boundary Series

| Repo | Layer | What It Does |
|---|---|---|
| [interpretation-boundary-lab](https://github.com/LalaSkye/interpretation-boundary-lab) | Upstream boundary | 10-rule admissibility gate for interpretations |
| [dual-boundary-admissibility-lab](https://github.com/LalaSkye/dual-boundary-admissibility-lab) | Full corridor | Dual-boundary model with pressure monitoring and C-sector rotation |
| [execution-boundary-lab](https://github.com/LalaSkye/execution-boundary-lab) | Execution boundary | Demonstrates cascading failures without upstream governance |
| [stop-machine](https://github.com/LalaSkye/stop-machine) | Control primitive | Deterministic three-state stop controller |
| [constraint-workshop](https://github.com/LalaSkye/constraint-workshop) | Control primitives | Execution gate, invariant litmus, stop machine |
| [csgr-lab](https://github.com/LalaSkye/csgr-lab) | Measurement | Contracted stability and drift measurement |
| [invariant-lock](https://github.com/LalaSkye/invariant-lock) | Drift prevention | Refuse execution unless version increments |
| [policy-lint](https://github.com/LalaSkye/policy-lint) | Policy validation | Deterministic linter for governance statements |
| [deterministic-lexicon](https://github.com/LalaSkye/deterministic-lexicon) | Vocabulary | Fixed terms, exact matches, no inference |

---

## License

MIT. See `LICENSE`.

---

## Authorship & Rights

All architecture, methods, and system designs in this repository are the original work of **Ricky Dean Jones** unless otherwise stated.
No rights to use, reproduce, or implement are granted without explicit permission beyond the terms of the repository licence.

**Author:** Ricky Dean Jones
**Repository owner:** [LalaSkye](https://github.com/LalaSkye)
**Status:** Active research / architecture work
**Part of:** [Execution Boundary Series](https://github.com/LalaSkye) — TrinityOS / AlvianTech

---

This repository demonstrates deterministic control using standard engineering techniques. No proprietary frameworks or external implementations are used.

