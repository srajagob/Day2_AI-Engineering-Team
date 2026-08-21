---
name: code-context-extraction
description: 'Extract focused source code context for engineering investigations. Use when tracing functions, classes, call paths, configuration references, stack traces, tests, or implementation boundaries.'
argument-hint: 'Provide the symbol, file, stack trace, test, or behavior to inspect'
---

# Code Context Extraction

## Purpose

Find the smallest useful code context needed to understand a behavior, failure, feature request, refactor, or documentation task.

## When to Use

Use this skill when an agent needs to:

- Trace a stack frame to the owning implementation
- Understand a function, class, module, or configuration path
- Connect tests to production code
- Identify implementation boundaries before editing
- Summarize code behavior for review or documentation

## Inputs

- File path, symbol, stack trace, error message, or test name
- Target behavior or question
- Known constraints or suspected component

## Procedure

1. Start from the most concrete anchor.
   - Prefer a failing test, stack frame, symbol, file path, or configuration key.
   - If the anchor only forwards or registers behavior, step to the nearest code that directly computes or controls it.

2. Read narrowly around the anchor.
   - Capture the owning function, class, module, or test case.
   - Avoid mapping unrelated project structure.

3. Identify dependencies and boundaries.
   - Note direct callers, callees, configuration values, external services, and test fixtures when relevant.
   - Mark boundaries where behavior is delegated to another component.

4. State the local hypothesis.
   - Describe what the code appears to do and what would disconfirm that understanding.
   - Identify the cheapest nearby check, such as a focused test or compile command.

5. Produce a context package.
   - Keep the summary short enough for another agent to use as input.
   - Include file or symbol references that are reviewable.

## Output Format

```text
Code Context Package
Anchor:
- <file, symbol, test, stack frame, or config key>

Owning Code Path:
- <component/function/class and role>

Relevant Dependencies:
- <direct dependency or boundary>

Observed Behavior:
- <what the code currently appears to do>

Local Hypothesis:
- <falsifiable statement>

Cheapest Check:
- <focused validation or inspection step>
```

## Quality Bar

- Keep the context bounded to the task.
- Prefer direct implementation code over broad architecture summaries.
- Do not recommend edits until the controlling code path is identified.
