---
name: failure-pattern-analysis
description: 'Analyze current engineering failures against historical failures and known patterns. Use when comparing logs, test failures, incidents, regressions, flaky tests, error messages, or validation failures.'
argument-hint: 'Provide the current failure details and any available history source'
---

# Failure Pattern Analysis

## Purpose

Compare a current failure with prior failures or known patterns so agents can distinguish recurring problems from new behavior.

## When to Use

Use this skill when an agent needs to:

- Compare a current error with historical failures
- Detect regression patterns
- Group related failures by symptom or component
- Identify flaky tests or recurring validation issues
- Summarize prior investigations for review

## Inputs

- Current failure symptoms
- Error messages, logs, or stack traces
- Test names and validation outputs
- Historical failure records, incident notes, issue links, or prior summaries
- Relevant component or configuration context

## Procedure

1. Define the current failure signature.
   - Capture exact error text, failing test names, affected component, environment, and timing.
   - Normalize volatile details such as timestamps, request IDs, and machine-specific paths.

2. Search or review bounded history.
   - Prefer known issue trackers, incident notes, test history, commit messages, and prior investigation records.
   - Keep the search tied to the current signature and affected component.

3. Compare failure dimensions.
   - Symptom: error text, status code, exception, assertion, timeout, or crash.
   - Context: component, environment, test suite, configuration, dependency, or recent change.
   - Outcome: known root cause, mitigation, fix, or unresolved status.

4. Classify the relationship.
   - Exact repeat: same symptom and same likely cause.
   - Similar pattern: same symptom family with different details.
   - Possible regression: previously fixed behavior appears again.
   - New failure: no strong historical match found.

5. Produce a pattern summary.
   - List strongest matches first.
   - Explain why each match is relevant.
   - Identify the next check that would confirm or reject the match.

## Output Format

```text
Failure Pattern Summary
Current Signature:
- <short normalized signature>

Historical Matches:
- <id or source>: <why it matches> | <known cause or resolution>

Classification:
- <exact repeat | similar pattern | possible regression | new failure>

Confidence:
- <high | medium | low> because <evidence>

Next Discriminating Check:
- <small check that confirms or rejects the match>
```

## Quality Bar

- Do not claim a root cause based only on similarity.
- Include enough evidence for a reviewer to judge the match.
- Prefer fewer high-quality matches over a long loose list.
