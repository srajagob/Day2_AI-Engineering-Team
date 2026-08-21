---
name: engineering-decision-record
description: 'Create reviewable engineering decision records from investigations, requirements, validation, refactoring, feature design, debugging findings, or documentation updates.'
argument-hint: 'Provide the decision, evidence, alternatives, risks, and validation results'
---

# Engineering Decision Record

## Purpose

Turn an engineering investigation or recommendation into a concise, reviewable decision record that teammates can evaluate later.

## When to Use

Use this skill when an agent needs to document:

- Debugging findings and proposed fixes
- Feature implementation decisions
- Requirement interpretations or gaps
- Refactoring tradeoffs
- Documentation changes based on technical evidence
- Validation outcomes and residual risk

## Inputs

- Decision or recommendation
- Evidence summary
- Code context
- Requirements or constraints
- Alternatives considered
- Validation results
- Risks, assumptions, and open questions

## Procedure

1. State the decision.
   - Use one clear sentence.
   - Avoid burying the decision in background detail.

2. Link the decision to evidence.
   - Summarize the key facts that support the decision.
   - Reference source artifacts where possible.

3. Record alternatives.
   - Include meaningful alternatives that were considered.
   - Explain why each was not selected.

4. Capture risk and assumptions.
   - Identify operational, test, design, maintainability, or requirement risks.
   - Separate assumptions from validated facts.

5. Record validation.
   - Note checks performed and results.
   - Identify remaining validation gaps.

6. Define follow-up.
   - List concrete next actions, owners, or unresolved questions when applicable.

## Output Format

```text
Engineering Decision Record
Decision:
- <one-sentence decision>

Context:
- <why this decision is needed>

Evidence:
- <fact or artifact reference>

Alternatives Considered:
- <alternative>: <reason not selected>

Validation:
- <check and result>

Risks and Assumptions:
- <risk or assumption>

Follow-up:
- <next action or none>
```

## Quality Bar

- Keep the record short enough to review quickly.
- Do not hide uncertainty; label assumptions and gaps clearly.
- Make the decision understandable without replaying the whole investigation.
