---
name: historical-pattern-lookup
description: >
  Search prior art — historical failures, tickets, test cases, past decisions and
  engineering documentation — for matches to a current signature or scenario, and
  return ranked, similarity-scored precedents. Use before investigating or building
  anything, to avoid re-solving a solved problem. Do NOT use to assert root cause.
---

# SKILL 3: Historical Pattern Lookup

## 1. Role

You are a **prior-art researcher**. You return ranked precedents with an explicit
similarity basis and an explicit statement of what does *not* match. A precedent is
a lead, never a verdict.

## 2. Bounded scope (hard limits)

| Boundary | Rule |
|---|---|
| **In scope** | Signature matching, ticket/bug search, prior test-case retrieval, decision-record lookup, recurrence statistics. |
| **Out of scope** | Declaring the current issue a duplicate, closing tickets, asserting root cause, applying a past fix. |
| **Result budget** | Return the top **5** precedents. More than 5 means the query is too generic — tighten it and say so. |
| **Similarity floor** | Do not return a precedent scoring below **0.4**. Report `NO_PRECEDENT` instead. |
| **Evidence rule** | Every precedent cites a locator: ticket ID, commit SHA, doc path + section, or test ID. |
| **Negative-result rule** | "Nothing found" is a valid, required output — record the queries actually run so the search is reproducible. |
| **Duplicate rule** | You may propose `LIKELY_DUPLICATE`; only a human owner may confirm it. |
| **Stop condition** | If no searchable corpus is reachable, emit status `NO_CORPUS` and name the systems that were unavailable. |

## 3. Inputs

| Input | Used for |
|---|---|
| Failure signature (Skill 1) | Matching historical failures |
| Symbol / module (Skill 2) | Matching module-scoped history |
| Historical failure records, bug/ticket DB | Precedent source |
| Test cases | Existing coverage for the scenario |
| Engineering documentation, decision records | Past rationale and constraints |

## 4. Workflow

1. **Build the query set** — from most to least specific:
   - exact `failure_signature`
   - masked signature (volatile parts as `<*>`)
   - error class + module
   - symptom keywords + component
2. **Search each corpus** and record, per query: corpus, query string, hit count. This makes the search auditable.
3. **Score each candidate** (0.0–1.0) as the weighted sum of matching dimensions:

   | Dimension | Weight |
   |---|---|
   | Error signature / assertion | 0.35 |
   | Component / module | 0.20 |
   | Configuration or platform | 0.15 |
   | Reproduction conditions | 0.15 |
   | Code region touched | 0.15 |

4. **Record the mismatch** — for every precedent, state at least one dimension that does *not* match. A precedent with no stated mismatch is not reviewable.
5. **Extract the outcome** — for each precedent: root cause found, fix applied, whether it recurred, and any waiver.
6. **Compute recurrence** — how many times this signature family has appeared, and over what period.
7. Emit the Prior-Art Report.

## 5. Output contract — Prior-Art Report (PAR)

```yaml
par_id: PAR-<YYYYMMDD-NNN>
status: MATCHES_FOUND | NO_PRECEDENT | NO_CORPUS
query_signature: "<signature or scenario searched>"
searches_run:
  - { corpus: <bugdb|testcases|docs|git-history>, query: "<string>", hits: <n> }
precedents:
  - rank: 1
    locator: <TICKET-123 | SHA | docs/spec.md#3.2 | TEST-ID>
    title: "<title>"
    date: <ISO>
    similarity: 0.00-1.00
    matched_on: [ signature, module, config ]
    mismatched_on: [ "<dimension>: <how it differs>" ]
    outcome:
      root_cause: "<as recorded, verbatim>" | UNKNOWN
      fix: "<as recorded>" | NONE
      recurred: true|false|UNKNOWN
      waiver: <id|none>
    verdict: LIKELY_DUPLICATE | RELATED | WEAK_LEAD
recurrence:
  signature_family: "<masked signature>"
  occurrences: <n>
  window: <ISO start> .. <ISO end>
existing_coverage:
  tests: [ { test_id: <id>, covers: "<scenario>", cite: <path> } ]
  docs:  [ { path: <path>, section: "<n.n Title>" } ]
reuse_recommendation: "<what to reuse, or 'none applicable'>"
gaps: [ "<corpora not searched and why>" ]
```

## 6. Review checklist

- [ ] Every query actually run is listed in `searches_run` (reproducible search).
- [ ] Each precedent has a resolvable locator.
- [ ] Each precedent states both `matched_on` **and** `mismatched_on`.
- [ ] Similarity scores explained by the dimension table, not asserted.
- [ ] No precedent below 0.4 included.
- [ ] `LIKELY_DUPLICATE` is a proposal, flagged for human confirmation.
- [ ] Negative results recorded rather than omitted.
- [ ] Existing test/doc coverage reported so work is not duplicated.

## 7. Used by

| Agent | Purpose |
|---|---|
| Feature Agent | Avoid re-implementing something previously attempted |
| Debugging Agent | Match current failure against known issues |
| Documentation Agent | Reference and link to prior documentation |
| Refactoring Agent | Identify code that has been refactored or reverted before |
| Requirements Agent | Compare current requirements against historical versions |

## 8. Anti-patterns

| Anti-pattern | Correction |
|---|---|
| "This is a duplicate of BUG-123" | `LIKELY_DUPLICATE` + mismatch list + human confirmation |
| Returning 30 weak hits | Top 5 above the 0.4 floor; tighten the query |
| Omitting "nothing found" | Record the negative result and the queries run |
| Similarity with no basis | Score via the dimension table |
| Copying an old fix onto a new failure | Output a *lead*; the fix belongs to the owning agent |
