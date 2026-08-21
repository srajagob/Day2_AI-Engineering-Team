# Documentation Agent Guide

## Purpose
The Documentation Agent creates meaningful engineering documentation by combining four skills:
- configuration-analysis
- log-evidence-parsing
- historical-pattern-lookup
- structured-report-generation

## Skill Pipeline
1. log-evidence-parsing
- Parse logs, errors, test outputs, and validation results.
- Extract key signals such as failure signatures, stack traces, statuses, and timestamps.

2. configuration-analysis
- Parse and compare configuration files.
- Highlight deviations from expected or baseline values.

3. historical-pattern-lookup
- Find similar failures, tests, and prior engineering decisions.
- Add supporting references to reduce repeated investigation.

4. structured-report-generation
- Assemble all evidence into a reviewable document.
- Rank findings by severity and confidence with citations.

## Meaningful Document Criteria
A document is meaningful when it is:
- Evidence-based: each claim has a source.
- Context-aware: includes configuration state and historical parallels.
- Actionable: includes validation status and next actions.
- Bounded: clear scope, time window, and known unknowns.

## Recommended Output Structure
- Title
- Scope
- Overall Status
- Findings (ranked by severity)
- Evidence
- Configuration Analysis
- Historical Pattern Match
- Validation Summary (confirmed, unconfirmed, blocked)
- Recommended Next Actions

## Example Summary
Status: partial

Key points:
- A recurring failure signature appears in recent logs.
- Current configuration deviates from baseline in two keys.
- A similar failure was previously resolved by correcting one config key.

Validation:
- Confirmed: failure signature and config drift.
- Unconfirmed: whether drift is the sole root cause.
- Blocked: missing one historical test artifact.

Next Actions:
- Restore baseline for the flagged keys.
- Re-run targeted tests.
- Attach missing historical artifact to complete validation.
