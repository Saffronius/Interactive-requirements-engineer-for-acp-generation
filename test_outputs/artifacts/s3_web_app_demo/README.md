# Policy Generation Session

**Generated:** 2025-08-16 23:15:04
**Original Prompt:** S3 read access for web application

## Contents

This directory contains a complete four-artifact policy generation session:

### Core Artifacts
- `artifacts.json` - Master file with all artifacts and metadata
- `read_back.md` - Human-readable summary and analysis
- `spec_dsl.json` - Machine-readable intent specification
- `baseline_policy.json` - Deterministic policy from canonizer
- `candidate_policy.json` - LLM-generated policy

### Analysis & Context
- `policy_comparison.md` - Side-by-side policy analysis
- `evidence_archive.json` - RAG context and citations
- `audit_trail.json` - Confidence scores and metrics
- `README.md` - This file

## Quick Stats

- **Extraction Confidence:** 85.0%
- **Generation Confidence:** 100.0%
- **Capabilities:** 1
- **Restrictions:** 0
- **Baseline Statements:** 0
- **Candidate Statements:** 3

## Usage

1. Review `read_back.md` for human understanding
2. Check `policy_comparison.md` for differences analysis
3. Deploy `baseline_policy.json` for safety or `candidate_policy.json` if validated
4. Reference `evidence_archive.json` for source documentation
