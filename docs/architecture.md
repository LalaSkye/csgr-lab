# CSGR-Lab Architecture

## Overview

CSGR-Lab (Contracted Stability & Drift Measurement) is a deterministic scoring and audit framework for evaluating LLM behaviour against formal contracts. Every run produces immutable evidence with tamper-evident hash chains.

## Design Principles

1. **Determinism** - Same inputs always produce the same outputs
2. **Immutability** - All records and results are frozen after creation
3. **Auditability** - Every scoring run generates chained evidence
4. **No hidden state** - Scoring has no side effects
5. **Minimal dependencies** - Core logic uses only stdlib + Pydantic

## Module Structure

```
csgr_lab/
|-- __init__.py          # Package root, version
|-- cli.py               # Typer CLI interface
|-- config/
|   |-- __init__.py
|   |-- settings.py      # Pydantic-settings configuration
|-- contracts/
|   |-- __init__.py
|   |-- types.py         # Enums, NewType aliases
|   |-- schema.py        # Pydantic frozen models (ClauseSpec, ContractSpec)
|   |-- validators.py    # Clause evaluation logic
|-- scoring/
|   |-- __init__.py
|   |-- engine.py        # ScoringEngine, ScoringRun
|-- drift/
|   |-- __init__.py
|   |-- detector.py      # DriftDetector, z-score analysis
|-- evidence/
    |-- __init__.py
    |-- logger.py         # EvidenceLogger, SHA-256 hash chain
```

## Data Flow

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

## Key Components

### Contracts (`contracts/`)

Contracts define behavioural expectations using Pydantic frozen models. Each `ContractSpec` contains one or more `ClauseSpec` entries that specify a metric, comparison operator, and threshold. Contracts are immutable once created.

### Scoring Engine (`scoring/`)

The `ScoringEngine` evaluates a contract against a set of measurements. It produces an immutable `ScoringRun` record containing the result, a deterministic input hash, and a timestamp. The `verify_determinism()` method confirms that repeated scoring produces identical outcomes.

### Evidence Logger (`evidence/`)

The `EvidenceLogger` writes append-only JSONL files where each record includes a SHA-256 hash linking it to the previous record. This creates a tamper-evident chain that can be verified with `verify_chain()`.

### Drift Detector (`drift/`)

The `DriftDetector` uses z-score analysis to compare current metric values against historical baselines. It reports whether a metric has regressed, improved, or remained stable, using a configurable z-score threshold.

### Configuration (`config/`)

All settings are managed through `pydantic-settings` with environment variable support using the `CSGR_` prefix. Defaults are provided for all values.

## CLI

The `csgr` CLI provides two commands:

- `csgr score <contract.json> <measurements.json>` - Score a contract and log evidence
- `csgr verify` - Verify the integrity of the evidence chain
- `csgr version` - Show version information

## Testing

Tests are organised by module in the `tests/` directory and use `pytest`. Run with:

```bash
pytest tests/ -v
```

## Relationship to Trinity OS

CSGR-Lab is a standalone reference implementation of the contracted stability measurement layer described in the Trinity OS governance framework. It demonstrates how deterministic contracts, immutable evidence, and drift detection work together to provide auditable AI oversight.
