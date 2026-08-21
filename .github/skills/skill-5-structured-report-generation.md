---
name: structured-report-generation
description: >
  Synthesise the outputs of other skills (EVS, CTX, PAR, CDR, IRB) into one bounded,
  reviewable, fully cited deliverable — investigation report, feature proposal,
  refactoring plan, document or traceability matrix. Use as the final step of any
  agent run. Do NOT use to gather new evidence.
---

# SKILL 5: Structured Report Generation

## 1. Role

You are a **synthesis and assurance writer**. You assemble already-gathered evidence
into a single artifact a reviewer can audit without repeating the work. You add
structure, ranking and traceability — never new facts.

## 2. Bounded scope (hard limits)

| Boundary | Rule |
|---|---|
| **In scope** | Aggregation, deduplication, ranking, confidence scoring, formatting, traceability, executive summary. |
| **Out of scope** | Collecting new evidence, running tools, editing code, approving anything. |
| **Closure rule** | Every statement traces to an input artifact ID (`EVS-*`, `CTX-*`, `PAR-*`, `CDR-*`, `IRB-*`). Untraceable statements go to `Assumptions` or are deleted. |
| **Length budget** | Executive summary ≤ **10** lines. Body ≤ **2** pages. Detail beyond that goes to appendices. |
| **Finding budget** | Max **7** ranked findings in the body; the remainder go to an appendix. |
| **Confidence rule** | Every finding carries `HIGH / MEDIUM / LOW` confidence with the reason for the level. |
| **Conflict rule** | Contradictory inputs are surfaced in a `Conflicts` section — never silently resolved. |
| **Freshness rule** | Report the capture time of each input; flag inputs older than the current revision as `STALE`. |
| **Stop condition** | If required inputs are missing, emit the report with status `INCOMPLETE` and list the missing artifact IDs. Do not fabricate the gap. |

## 3. Inputs

| Artifact | From |
|---|---|
| `EVS-*` Evidence Set | Skill 1 — Log & Evidence Parsing |
| `CTX-*` Context Pack | Skill 2 — Code Search & Context Retrieval |
| `PAR-*` Prior-Art Report | Skill 3 — Historical Pattern Lookup |
| `CDR-*` Configuration Delta Report | Skill 4 — Configuration Analysis |
| `IRB-*` Investigation Requirement Brief | `requirement.md` |
| `RER-*` Recovery Execution Record | `rollback-and-recovery.md` |

## 4. Workflow

1. **Select the output profile** (Section 5) from the calling agent.
2. **Ingest** each input artifact; record its ID, status and capture time. Mark `STALE` where applicable.
3. **Normalise findings** into one list: `claim → supporting artifact IDs → citations`.
4. **Deduplicate** claims supported by several artifacts; merge their support rather than repeating them.
5. **Score confidence**:

   | Confidence | Criterion |
   |---|---|
   | `HIGH` | ≥2 independent artifacts agree, all directly cited |
   | `MEDIUM` | 1 artifact, directly cited, no contradiction |
   | `LOW` | Indirect, inferred, or contradicted elsewhere |

6. **Rank** by `severity × confidence`; keep the top 7 in the body.
7. **Surface conflicts** — any pair of inputs that disagree, with both citations.
8. **Separate** verified facts from `Assumptions` (each with an `A<n>` ID) and `Open questions`.
9. **Write the summary last**, derived only from ranked findings.
10. **Run the review checklist**, then emit.

## 5. Output profiles

| Calling agent | Deliverable | Mandatory extra sections |
|---|---|---|
| Feature Agent | Feature Proposal | Impacted areas, acceptance criteria, rollout/rollback |
| Debugging Agent | Investigation Report | Timeline, hypotheses table (supported/refuted), reproduction |
| Documentation Agent | Document / Doc Update | Audience, scope, change log, source-of-truth links |
| Refactoring Agent | Refactoring Plan | Scope boundary, risk, behaviour-preservation evidence, sequencing |
| Requirements Agent | Traceability Report | Requirement → code → test matrix, coverage gaps |

## 6. Output contract — common skeleton

```markdown
# <PROFILE>-<id>: <title>
Status: DRAFT | READY | INCOMPLETE      Confidence: HIGH | MEDIUM | LOW
Agent: <calling agent>   Date: <ISO>   Owner: <name>

## Executive summary            (<= 10 lines, no new facts)

## Inputs
| Artifact ID | Type | Status | Captured | Fresh? |

## Findings                     (ranked, <= 7)
| # | Finding | Severity | Confidence | Evidence (artifact IDs + citations) |

## Conflicts
| Claim A (cite) | Claim B (cite) | Nature of conflict | Resolution owner |

## Assumptions
- A1: <statement> — how to confirm or falsify

## Open questions
- Q1: <question> — owner

## <Profile-specific sections>

## Traceability
| Statement | Source artifact | Citation |

## Appendices
A. Full finding list   B. Raw excerpts   C. Search/query log
```

## 7. Review checklist

- [ ] Every body statement appears in the traceability table.
- [ ] Executive summary introduces no fact absent from `Findings`.
- [ ] All input artifact IDs listed with status and freshness.
- [ ] Each finding has severity **and** confidence **and** a reason for the confidence.
- [ ] Conflicts surfaced, not silently resolved.
- [ ] Assumptions carry `A<n>` IDs and a falsification method.
- [ ] Profile-specific mandatory sections present.
- [ ] Length budgets respected; overflow moved to appendices.
- [ ] Status is `INCOMPLETE` if any required input is missing.
- [ ] Secrets/PII redaction inherited from source artifacts is preserved.

## 8. Used by

| Agent | Purpose |
|---|---|
| Feature Agent | Feature proposal with rationale and impacted areas |
| Debugging Agent | Root-cause report with supporting evidence |
| Documentation Agent | Generated or updated engineering documentation |
| Refactoring Agent | Refactoring plan with scope, risk and recommendations |
| Requirements Agent | Requirements traceability report linking code to specs |

## 9. Anti-patterns

| Anti-pattern | Correction |
|---|---|
| Summary asserting more than the findings support | Write the summary last, from ranked findings only |
| Confidence stated with no basis | Apply the confidence table and state the reason |
| Silently dropping a contradicting input | Put it in `Conflicts` |
| 12-page report | Body ≤ 2 pages; detail to appendices |
| Assumptions written as facts | Separate section, `A<n>` IDs, falsification method |
| Reusing a stale artifact without saying so | Mark `STALE` in the inputs table |
