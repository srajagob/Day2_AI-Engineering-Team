# Integration Guide — Documentation Workflow

**Audience:** Engineering Tech Lead
**Status:** PUBLISHED
**Owner:** Documentation Agent Team

---

## 1. What Was Integrated

The existing `documentation-agent.agent.md` now drives a 5-phase automated
documentation pipeline implemented in `workflow/doc_workflow_runner.py`.

The workflow runs as a **linear state machine**. Every phase is an explicit state
transition — no phase can be skipped, and Sphinx is never invoked before docstrings
are written.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  documentation-agent.agent.md                   │
│  (Section 9 — Automated Workflow Integration)                   │
│                                                                  │
│   Phase map  ──►  doc_workflow_runner.py  (state machine)       │
│                        │                                        │
│           ┌────────────▼────────────────────────┐              │
│           │  WorkflowState  (mutable data bus)   │              │
│           └──┬──────┬──────┬──────┬──────────────┘              │
│              │      │      │      │                              │
│           Phase1  Phase2  Phase3  Phase4  Phase5                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Phase → Skill → Artifact Map

| # | Phase | Skill(s) | Output |
|---|---|---|---|
| 1 | Scope Identification | Skill 2, 3 | `scope_manifest` JSON |
| 2 | File / Logic Analysis | Skill 2 | `code_map` in-memory |
| 3 | Inline Doc Application | Skill 5 | Patched `.py` files with docstrings |
| 4 | Sphinx Automation | Skill 4, 5 | `.rst` files + HTML build |
| 5 | Review & Maintenance | Skill 1, 5 | `coverage_report.json` |

---

## 4. Key Design Decisions

**Docstrings before Sphinx** — Phase 3 (`INLINE_DOC`) is a required predecessor
of Phase 4 (`SPHINX_BUILD`) in the `TRANSITIONS` dict. If Phase 3 fails, the
runner sets `Phase.FAILED` and aborts; Sphinx is never invoked on undocumented source.

**Sphinx-optional** — If `sphinx-apidoc` / `sphinx-build` are not on `$PATH`,
the runner generates `.rst` files directly from the scope manifest and logs a
warning. The workflow still reaches `DONE`.

**Non-destructive AST injection** — Docstrings are inserted using line-index
arithmetic in reverse order. The original source layout is preserved; only the
docstring lines are added.

**Error isolation** — `SyntaxError` in a single source file is a WARNING (the
file is skipped); all other exceptions are ERROR and abort the workflow.

---

## 5. How to Run

### Prerequisites
```bash
python3 --version          # 3.9+ required (ast.unparse)
pip install sphinx          # optional — enables HTML output
```

### Test run on the sample codebase
```bash
cd Day2_AI-Engineering-Team

python3 workflow/doc_workflow_runner.py \
    workflow/sample_codebase \
    --output doc_output
```

### Expected output
```
workflow.log           — full phase-by-phase execution trace
coverage_report.json   — { coverage_before_pct, coverage_after_pct, patched_files, ... }
docs/source/           — .rst files ready for Sphinx or browser
docs/build/            — HTML (if sphinx-build available)
```

---

## 6. Demonstrating the Test Run

The `workflow/sample_codebase/` package contains two modules:

| Module | Documented | Undocumented |
|---|---|---|
| `log_parser.py` | `LogEntry`, `is_error`, `is_warning` | `parse_eda_log`, `extract_errors`, `extract_warnings`, `group_by_code`, `top_error_codes`, `filter_by_stage`, `summarise` |
| `test_result_analyzer.py` | `TestResult`, `RegressionRun`, `passed` | `parse_csv_results`, `parse_json_results`, `group_failures_by_error_code`, `top_failure_codes`, `compare_runs`, `slowest_tests`, `filter_by_tag`, `build_summary_report` |

After a successful run, `coverage_report.json` will show:
```json
{
  "coverage_before_pct": <X>,
  "coverage_after_pct":  <Y>,   // Y > X — docstrings injected
  "patched_files": ["log_parser.py", "test_result_analyzer.py"],
  ...
}
```

---

## 7. Acceptance Criteria Verification

| Criterion | Where to verify |
|---|---|
| Workflow follows all 5 phases | `workflow.log` — all 5 phase headers present in order |
| Docstrings written before Sphinx | `workflow.log` — Phase 3 line appears before Phase 4 line |
| Coverage improves | `coverage_report.json` — `coverage_after_pct > coverage_before_pct` |
| `.rst` files generated | `doc_output/docs/source/*.rst` exists |
| Test run exits 0 | Shell: `echo $?` returns `0` |

---

## 8. Files Delivered

```
workflow/
├── doc_workflow_runner.py          ← state machine (5 phases, error handling, logging)
├── INTEGRATION.md                  ← this document
└── sample_codebase/
    ├── __init__.py
    ├── log_parser.py               ← EDA log parser (partially undocumented)
    └── test_result_analyzer.py     ← Regression result analyzer (partially undocumented)

.github/agents/
└── documentation-agent.agent.md   ← updated: Section 9 added (workflow integration)
```
