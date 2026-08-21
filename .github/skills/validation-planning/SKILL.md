---
name: validation-planning
description: 'Plan focused engineering validation for hypotheses, bug fixes, refactors, features, and requirements. Use when selecting tests, commands, expected outcomes, falsifying signals, or review evidence.'
argument-hint: 'Describe the change, hypothesis, requirement, or failure to validate'
---

# Validation Planning

## Purpose

Define how to verify an engineering hypothesis, change, requirement, or fix with bounded and reviewable checks.

## When to Use

Use this skill when an agent needs to:

- Choose tests for a bug fix or feature change
- Validate a debugging hypothesis
- Check that requirements are satisfied
- Confirm that a refactor preserved behavior
- Interpret validation results for review

## Inputs

- Hypothesis, requirement, or proposed change
- Relevant tests, test cases, or validation commands
- Expected behavior and known failure behavior
- Constraints such as environment, time, or unavailable systems

## Procedure

1. State the validation target.
   - Identify exactly what must be proven or disproven.
   - Keep the target tied to one behavior, requirement, or risk.

2. Select the narrowest meaningful check.
   - Prefer a focused failing test, unit test, typecheck, lint check, or command for the touched area.
   - Use broader suites only after the narrow check passes or when the change affects shared behavior.

3. Define expected and falsifying signals.
   - Expected signal: what should happen if the hypothesis is correct.
   - Falsifying signal: what would show the hypothesis is wrong or incomplete.

4. Sequence checks by cost and confidence.
   - Run cheap, behavior-specific checks first.
   - Add integration, regression, or full-suite checks when risk justifies them.

5. Record results and next action.
   - Summarize command results, pass/fail status, and remaining risk.
   - If validation fails, identify whether it supports the current hypothesis or points elsewhere.

## Output Format

```text
Validation Plan
Target:
- <behavior, requirement, fix, or hypothesis>

Checks:
- <command or manual check>: <why this check matters>

Expected Signal:
- <what success looks like>

Falsifying Signal:
- <what failure would prove or suggest>

Result Recording:
- <how to summarize the outcome for review>

Residual Risk:
- <known gap or none>
```

## Quality Bar

- Every check should map to a specific behavior or risk.
- Do not treat a passing broad build as proof of behavior unless it exercises the behavior.
- Capture unavailable validation honestly.
