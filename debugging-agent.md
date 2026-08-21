# Debugging Agent — EDA / Silicon Engineering

## Responsibility

Investigate failures in EDA tool flows (synthesis, place-and-route, timing, DRC/LVS) by parsing long tool logs, correlating error signatures with source RTL and configuration, and producing a ranked root-cause report — so engineers do not have to manually grep through multi-GB log files.

---

## Scope (Bounded)

| In Scope | Out of Scope |
|---|---|
| Fusion Compiler, PrimeTime, VCS, SpyGlass logs | RTL design review or code generation |
| Timing violations, DRC/LVS errors, synthesis failures | Full flow automation or job scheduling |
| Configuration mismatch detection | Fixing the RTL or constraints directly |
| Historical failure matching | Deployment or signoff decisions |

---

## Inputs

| Input | Examples |
|---|---|
| **Logs** | `fc_shell.log`, `pt_shell.log`, `vcs_compile.log`, `spyglass.rpt` |
| **Error messages** | `Error: MV-016`, `Warning: PSYN-040`, `LINT: W143` |
| **Test results** | Regression pass/fail tables, NBJOBS run summaries |
| **Source code** | RTL (.v, .sv), SDC constraint files |
| **Configuration** | `app_options.rpt`, tool setup scripts, `.tcl` overrides |
| **Historical failures** | Past HSD tickets, known issue databases, archived logs |
| **Validation results** | Timing closure reports, DRC clean status |
| **Engineering documentation** | Design specs, flow guides, tapeout checklists |

---

## Skills Used

| Skill | How this agent uses it |
|---|---|
| **Skill 1: Log & Evidence Parsing** | Parse EDA tool logs to extract error codes, stack traces, stage timestamps, and severity-ranked messages |
| **Skill 2: Code Search & Context Retrieval** | Locate the RTL module, SDC constraint, or TCL hook referenced in the error |
| **Skill 3: Historical Pattern Lookup** | Match current error signature against known failures in past tickets or archived runs |
| **Skill 4: Configuration Analysis** | Diff `app_options` or tool setup between a passing and failing run to surface unexpected overrides |
| **Skill 5: Structured Report Generation** | Produce a ranked root-cause report with error evidence, suspected code/config location, and historical match |

---

## Workflow

```
1. PARSE       → Skill 1: Extract all ERROR/WARNING lines from logs; rank by stage and severity
2. LOCATE      → Skill 2: Map top errors to RTL module, SDC file, or tool hook in source
3. MATCH       → Skill 3: Search historical failures for the same error code or message pattern
4. DIFF CONFIG → Skill 4: Compare configuration between current run and last known-good run
5. REPORT      → Skill 5: Output ranked root-cause hypotheses with supporting evidence
```

---

## Output

A **Root Cause Report** containing:

1. **Top error summary** — error code, tool stage, first occurrence timestamp
2. **Suspected location** — RTL module / SDC file / TCL hook with line reference
3. **Configuration delta** — any `app_options` or tool-setting change vs baseline
4. **Historical match** — closest past failure with resolution (if found)
5. **Confidence ranking** — High / Medium / Low per hypothesis

---

## Example Scenario

**Symptom:** Fusion Compiler run fails at clock tree synthesis with `Error: CTS-018`

| Step | Agent Action |
|---|---|
| Parse | Extracts `CTS-018` from `fc_shell.log` at stage `clock_opt`, timestamp 02:14:33 |
| Locate | Finds `set_clock_tree_options` in `cts_setup.tcl` referencing clock `pll_clk` |
| Match | Historical lookup returns HSD ticket #4521789 — same error, root cause was missing `set_clock_sense` |
| Config Diff | Finds `cts.constraint_mapping_mode` changed from `default` to `strict` vs last passing run |
| Report | Hypothesis 1 (High): Missing `set_clock_sense` on `pll_clk`. Hypothesis 2 (Medium): `constraint_mapping_mode` override causing stricter validation |

---

## Design Principles

- **Bounded:** The agent investigates and reports — it does not modify RTL, constraints, or flow scripts
- **Reviewable:** Every finding cites the exact log line, file, and historical reference it came from
- **Reusable:** All 5 skills are shared with other agents — no agent-specific tooling required
