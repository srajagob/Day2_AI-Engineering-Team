---
name: evidence-collection
description: 'Collect and organize engineering investigation evidence. Use when working with test results, logs, error messages, source code, configuration, validation results, or documentation before debugging, feature planning, requirements analysis, or review.'
argument-hint: 'Describe the investigation question and provide available artifacts or paths'
---

# Evidence Collection

## Purpose

Gather bounded, reviewable evidence for an engineering investigation before drawing conclusions or proposing changes.

## When to Use

Use this skill when an agent needs to understand what is known from concrete artifacts such as:

- Test results
- Logs
- Error messages
- Source code
- Configuration
- Historical failures
- Test cases
- Validation results
- Engineering documentation

## Inputs

- Investigation question or task goal
- Artifact paths, snippets, or summaries
- Known failing behavior or expected behavior
- Constraints from the engineer or team

## Procedure

1. Identify the investigation boundary.
   - State the component, behavior, test, or requirement being investigated.
   - Avoid collecting unrelated project-wide context.

2. Inventory the available artifacts.
   - Group artifacts by type: tests, logs, source, config, docs, history, validation.
   - Preserve file names, commands, timestamps, links, or other traceable references when available.

3. Extract factual signals.
   - Record exact errors, observed outputs, config values, and test names.
   - Separate facts from assumptions, guesses, and proposed next steps.

4. Note missing evidence.
   - Identify the smallest missing artifact that would change the investigation outcome.
   - Prefer nearby tests, direct logs, or specific source files over broad searches.

5. Produce an evidence summary.
   - Keep it concise and reviewable.
   - Include enough detail for another engineer or agent to verify the evidence.

## Output Format

```text
Evidence Summary
Scope:
- <component, behavior, or question>

Known Facts:
- <fact with source reference>

Artifacts Reviewed:
- <artifact type>: <path, command, or source>

Assumptions:
- <assumption or none>

Missing Evidence:
- <smallest useful missing item>

Recommended Next Check:
- <bounded validation or inspection step>
```

## Quality Bar

- Every major claim should trace back to an artifact.
- Do not mix evidence with recommendations unless clearly labeled.
- Do not infer root cause from symptoms alone.
