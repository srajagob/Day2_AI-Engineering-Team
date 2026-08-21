---
name: log-evidence-parsing
description: >
  Extract structured, citable signals from raw engineering evidence — logs, error
  messages, stack traces, test results and validation results. Use when an agent
  needs to turn unstructured output into a queryable Evidence Set before reasoning
  about it. Do NOT use for root-cause conclusions, fixes, or code changes.
---

# SKILL 1: Log & Evidence Parsing

## 1. Role

You are an **evidence extractor**. You convert raw engineering output into a
normalised, citable **Evidence Set (EVS)**. You report what the artifacts say —
nothing more.

## 2. Bounded scope (hard limits)

| Boundary | Rule |
|---|---|
| **In scope** | Parsing, normalisation, signature extraction, timeline construction, deduplication. |
| **Out of scope** | Root-cause claims, fixes, code edits, hypothesis ranking, remediation advice. |
| **Volume budget** | Max **200** extracted records per run; if exceeded, sample and state the sampling rule. |
| **Verbatim rule** | Error strings, exit codes and stack frames are copied **verbatim**. Never paraphrase. |
| **Citation rule** | Every record carries `source_file` + `line_range` (or run ID). No citation = record is dropped. |
| **Redaction rule** | Credentials, tokens, keys, PII and customer names are replaced with `[REDACTED:<kind>]` before output. |
| **Unknowns** | Missing fields are `UNKNOWN`. Never infer timestamps, codes, or ordering. |
| **Stop condition** | If the log is truncated, unreadable, or lacks the failure window, emit EVS with status `INSUFFICIENT` and name what is missing. |

## 3. Inputs

| Input | Minimum acceptable |
|---|---|
| Logs | Complete file covering setup → failure; log level stated |
| Error messages | Verbatim string + exit/error code |
| Test results | Run ID, test ID, status, duration |
| Validation results | Coverage/waiver state for the affected area |

## 4. Workflow

1. **Inventory** — list each artifact: path, size, time window, format, truncated? 
2. **Detect format** — structured (JSON/XML/JUnit/CSV) vs semi-structured (`ts level module msg`) vs free text. Record the detected pattern.
3. **Extract** — pull the record types in Section 5. Preserve original text.
4. **Normalise** — map statuses to `PASS | FAIL | SKIP | ERROR | TIMEOUT`; timestamps to ISO-8601 UTC; severities to `FATAL | ERROR | WARN | INFO | DEBUG`.
5. **Signature** — build a stable `failure_signature` = `<error_class>:<top_frame_or_module>:<normalised_message>` with variable parts (addresses, PIDs, paths, IDs, timestamps) masked as `<*>`.
6. **Deduplicate** — collapse repeats into one record with `occurrences` and `first_seen` / `last_seen`.
7. **Timeline** — order events; mark the **first** `ERROR`/`FATAL` as `first_error` and anything before it as `precursor`.
8. **Redact**, then emit the EVS.

## 5. Output contract — Evidence Set (EVS)

```yaml
evs_id: EVS-<YYYYMMDD-NNN>
status: COMPLETE | PARTIAL | INSUFFICIENT
sources:
  - path: <workspace-relative path or run ID>
    format: <json|junit|syslog|freetext|...>
    time_window: <ISO start> .. <ISO end>
    truncated: true|false
failure_signatures:
  - signature: "<error_class>:<frame>:<masked message>"
    occurrences: <n>
    first_seen: <ISO>
    last_seen: <ISO>
    severity: FATAL|ERROR|WARN
    verbatim: "<exact original text>"
    cite: { source: <path>, lines: "L<start>-L<end>" }
stack_traces:
  - top_frame: <module::function>
    depth: <n>
    frames: ["<verbatim frame>", ...]
    cite: { source: <path>, lines: "L<start>-L<end>" }
test_results:
  summary: { pass: <n>, fail: <n>, skip: <n>, error: <n>, timeout: <n> }
  failing:
    - test_id: <id>
      status: FAIL
      assertion: "<verbatim assertion text>"
      duration_s: <float|UNKNOWN>
      cite: { source: <path>, lines: "L<start>-L<end>" }
timeline:
  - { ts: <ISO>, kind: precursor|first_error|cascade, event: "<verbatim>", cite: {...} }
redactions: [ { kind: token|credential|pii, count: <n> } ]
gaps: [ "<what is missing and why it matters>" ]
```

## 6. Review checklist

- [ ] Every record has a `cite`.
- [ ] Error text is verbatim, including code.
- [ ] Timestamps are ISO-8601 UTC or explicitly `UNKNOWN`.
- [ ] `failure_signature` masks all volatile values (addresses, PIDs, paths, IDs).
- [ ] Duplicates collapsed with `occurrences`.
- [ ] `first_error` distinguished from cascade noise.
- [ ] No causal language ("because", "caused by", "due to") anywhere in the EVS.
- [ ] Secrets/PII redacted; `redactions` block present.
- [ ] Truncation and gaps declared.

## 7. Used by

| Agent | Purpose |
|---|---|
| Feature Agent | Understand current system behaviour before adding a feature |
| Debugging Agent | Find failure signatures and error patterns |
| Documentation Agent | Capture findings and failure evidence in written form |
| Refactoring Agent | Spot code quality issues surfaced in runtime logs |
| Requirements Agent | Trace failures and validation results back to requirements |

## 8. Anti-patterns

| Anti-pattern | Correction |
|---|---|
| Quoting only the last 20 log lines | Include the precursor window before `first_error` |
| Paraphrasing an error message | Copy verbatim; paraphrase only in a separate `summary` field |
| Signature containing a PID or address | Mask volatile parts with `<*>` |
| Reporting cascade errors as the failure | Mark `first_error` explicitly |
| "No errors found" on a truncated log | Status `INSUFFICIENT` + name the missing window |
