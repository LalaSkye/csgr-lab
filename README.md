![CI](https://github.com/LalaSkye/csgr-lab/actions/workflows/ci.yml/badge.svg)

# csgr-lab

Contracted Stability & Drift Measurement for LLMs. Deterministic scoring, auditable evidence, reproducible runs.

**v0.1.0** | MIT License

**This is an audit and evidence tool, not a framework.** It does not train models, score alignment, or provide recommendations. It evaluates LLM behaviour against formal contracts and produces tamper-evident evidence.

## Why this exists

If you cannot measure whether a system's behaviour has drifted from its contracted specification, you cannot govern it. Most LLM evaluation tools focus on quality metrics. This tool focuses on contract conformance: did the system do what it was specified to do, and can you prove it?

Every scoring run produces immutable, hash-chained evidence. Same inputs always produce the same scores.

## What it does

- Evaluates LLM outputs against formal `ContractSpec` definitions
- Produces deterministic scores with fail-closed control (missing data → failure, not default)
- Logs all results to append-only JSONL with SHA-256 hash chains
- Detects drift using z-score analysis against historical baselines
- Provides a CLI for scoring and evidence verification

## Data flow

```
ContractSpec + Measurements
        |
        v
  ScoringEngine.score()
        |
        v
  ScoringRun (immutable)
        |
        +---> EvidenceLogger.log()  ---> JSONL with hash chain
        |
        +---> DriftDetector.analyze() ---> DriftReport
```

## Quickstart

```bash
pip install .

# Score a contract against measurements
csgr score contract.json measurements.json

# Verify evidence chain integrity
csgr verify

# Show version
csgr version
```

## Module structure

| Module | Purpose |
|---|---|
| `contracts/` | Pydantic frozen models defining behavioural expectations (ClauseSpec, ContractSpec) |
| `scoring/` | Deterministic scoring engine producing immutable ScoringRun records |
| `evidence/` | Append-only JSONL logger with SHA-256 hash chain for tamper-evident audit |
| `drift/` | Z-score analysis for detecting regression or improvement against baselines |
| `config/` | Pydantic-settings configuration with `CSGR_` environment variable prefix |

## Design constraints

- **Deterministic:** same inputs → same outputs, verified by `verify_determinism()`
- **Immutable:** all records and results are frozen after creation
- **Auditable:** every run generates chained evidence with SHA-256 hashes
- **Fail-closed:** missing or malformed inputs produce errors, not defaults
- **Minimal:** core logic uses stdlib + Pydantic only

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Relationship to other repositories

`csgr-lab` sits at the audit and evidence layer of the control stack. It consumes outputs from systems governed by authority gates and commit boundaries, and produces the tamper-evident evidence trail that proves contract conformance.

## License

MIT
