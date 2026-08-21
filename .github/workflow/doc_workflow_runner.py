#!/usr/bin/env python3
"""
doc_workflow_runner.py — Documentation Workflow State Machine
=============================================================
Implements the 5-phase automated documentation workflow for the Documentation Agent.

Phases
------
1. SCOPE_IDENTIFICATION  — scan codebase, identify undocumented symbols
2. FILE_ANALYSIS         — deep AST parse, build annotated code map
3. INLINE_DOC            — generate and inject Google-style docstrings
4. SPHINX_BUILD          — run sphinx-apidoc + sphinx-build (or fallback to .rst)
5. REVIEW                — measure coverage delta, emit maintenance report

Usage
-----
    python3 doc_workflow_runner.py <target_dir> [--output <out_dir>]

Example
-------
    python3 doc_workflow_runner.py workflow/sample_codebase --output doc_output
"""

import ast
import json
import logging
import datetime
import shutil
import subprocess
import sys
from enum import Enum, auto
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# STATE MACHINE DEFINITION
# ─────────────────────────────────────────────────────────────────────────────

class Phase(Enum):
    SCOPE_IDENTIFICATION = "scope_identification"
    FILE_ANALYSIS        = "file_analysis"
    INLINE_DOC           = "inline_doc"
    SPHINX_BUILD         = "sphinx_build"
    REVIEW               = "review"
    DONE                 = "done"
    FAILED               = "failed"


# Valid phase transitions
TRANSITIONS: Dict[Phase, Phase] = {
    Phase.SCOPE_IDENTIFICATION: Phase.FILE_ANALYSIS,
    Phase.FILE_ANALYSIS:        Phase.INLINE_DOC,
    Phase.INLINE_DOC:           Phase.SPHINX_BUILD,
    Phase.SPHINX_BUILD:         Phase.REVIEW,
    Phase.REVIEW:               Phase.DONE,
}


@dataclass
class WorkflowState:
    """Mutable state object passed through every phase of the pipeline."""
    target_dir:      Path
    output_dir:      Path
    current_phase:   Phase                = Phase.SCOPE_IDENTIFICATION
    scope_manifest:  Dict[str, Any]       = field(default_factory=dict)
    code_map:        Dict[str, Any]       = field(default_factory=dict)
    patched_files:   List[str]            = field(default_factory=list)
    sphinx_output:   str                  = ""
    coverage_report: Dict[str, Any]       = field(default_factory=dict)
    errors:          List[str]            = field(default_factory=list)
    log_path:        Path                 = Path("workflow.log")


# ─────────────────────────────────────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging(log_path: Path) -> logging.Logger:
    """Configure dual-target logger (file=DEBUG, console=INFO)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("doc_workflow")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — SCOPE IDENTIFICATION
# Skill mapping: Skill 2 (Code Search), Skill 3 (Historical Pattern Lookup)
# ─────────────────────────────────────────────────────────────────────────────

def phase_scope_identification(state: WorkflowState, log: logging.Logger) -> None:
    """Scan target_dir for Python files; build a scope manifest of undocumented symbols."""
    log.info("═══ Phase 1: Scope Identification ═══")

    manifest: Dict[str, Any] = {
        "scanned_at":             datetime.datetime.utcnow().isoformat() + "Z",
        "target_dir":             str(state.target_dir),
        "files":                  [],
        "total_symbols":          0,
        "undocumented_symbols":   0,
        "initial_coverage_pct":   0.0,
    }

    py_files = sorted(state.target_dir.rglob("*.py"))
    if not py_files:
        raise FileNotFoundError(f"No Python (.py) files found in {state.target_dir}")

    for py_file in py_files:
        rel = str(py_file.relative_to(state.target_dir))
        log.debug(f"  Scanning: {rel}")
        source = py_file.read_text(encoding="utf-8")

        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError as exc:
            log.warning(f"  Skipping {rel} — SyntaxError: {exc}")
            continue

        file_entry: Dict[str, Any] = {"path": rel, "symbols": []}

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            has_doc = bool(
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            )
            sym: Dict[str, Any] = {
                "name":          node.name,
                "type":          type(node).__name__,
                "line":          node.lineno,
                "has_docstring": has_doc,
            }
            file_entry["symbols"].append(sym)
            manifest["total_symbols"] += 1
            if not has_doc:
                manifest["undocumented_symbols"] += 1
                log.debug(f"    MISSING DOC: {type(node).__name__} '{node.name}' line {node.lineno}")

        manifest["files"].append(file_entry)

    total = manifest["total_symbols"]
    undoc = manifest["undocumented_symbols"]
    cov   = round(100.0 * (total - undoc) / total, 1) if total else 0.0
    manifest["initial_coverage_pct"] = cov
    state.scope_manifest = manifest

    log.info(
        f"  Files={len(manifest['files'])}  Symbols={total}  "
        f"Undocumented={undoc}  Coverage={cov}%"
    )


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — FILE / LOGIC ANALYSIS
# Skill mapping: Skill 2 (Code Search & Context Retrieval)
# ─────────────────────────────────────────────────────────────────────────────

def _arg_names(node: ast.FunctionDef) -> List[str]:
    args = node.args
    names: List[str] = [a.arg for a in args.args if a.arg not in ("self", "cls")]
    if args.vararg:
        names.append(f"*{args.vararg.arg}")
    if args.kwarg:
        names.append(f"**{args.kwarg.arg}")
    return names


def _annotation(ann: Optional[ast.expr]) -> Optional[str]:
    if ann is None:
        return None
    try:
        return ast.unparse(ann)
    except Exception:
        return None


def phase_file_analysis(state: WorkflowState, log: logging.Logger) -> None:
    """Deep AST parse: extract signatures, return types, call patterns, class hierarchy."""
    log.info("═══ Phase 2: File / Logic Analysis ═══")
    code_map: Dict[str, Any] = {}

    for file_entry in state.scope_manifest["files"]:
        py_file = state.target_dir / file_entry["path"]
        source  = py_file.read_text(encoding="utf-8")

        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue

        file_map: Dict[str, Any] = {"module_docstring": None, "symbols": {}}

        # Module-level docstring
        if (tree.body
                and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Constant)
                and isinstance(tree.body[0].value.value, str)):
            file_map["module_docstring"] = tree.body[0].value.value[:120]

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args   = _arg_names(node)
                ret    = _annotation(node.returns)
                calls: List[str] = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        try:
                            calls.append(ast.unparse(child.func))
                        except Exception:
                            pass
                file_map["symbols"][node.name] = {
                    "type":        "function",
                    "line":        node.lineno,
                    "args":        args,
                    "return_type": ret,
                    "calls":       list(dict.fromkeys(calls))[:8],
                    "is_async":    isinstance(node, ast.AsyncFunctionDef),
                }
                log.debug(f"  {file_entry['path']}::{node.name}({', '.join(args)}) -> {ret}")

            elif isinstance(node, ast.ClassDef):
                bases: List[str] = []
                for b in node.bases:
                    try:
                        bases.append(ast.unparse(b))
                    except Exception:
                        pass
                file_map["symbols"][node.name] = {
                    "type":  "class",
                    "line":  node.lineno,
                    "bases": bases,
                }

        code_map[file_entry["path"]] = file_map

    state.code_map = code_map
    log.info(f"  Analysed {len(code_map)} file(s)")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 — INLINE DOC APPLICATION
# Skill mapping: Skill 5 (Structured Report Generation)
# ─────────────────────────────────────────────────────────────────────────────

def _build_docstring(name: str, sym: Dict[str, Any], body_indent: str) -> str:
    """Construct a Google-style docstring template from AST-derived symbol metadata."""
    lines: List[str] = ['"""']
    summary = name.replace("_", " ").capitalize() + "."
    lines.append(summary)

    if sym["type"] == "function":
        args = sym.get("args", [])
        ret  = sym.get("return_type")
        if args:
            lines += ["", "Args:"]
            for a in args:
                lines.append(f"    {a}: TODO — describe parameter.")
        if ret and ret not in ("None", "none"):
            lines += ["", "Returns:", f"    {ret}: TODO — describe return value."]
        lines += ["", "Raises:", "    TODO — list exceptions this function may raise."]

    elif sym["type"] == "class":
        bases = sym.get("bases", [])
        if bases:
            lines += ["", f"Inherits from: {', '.join(bases)}."]
        lines += ["", "Attributes:", "    TODO — list public attributes."]

    lines.append('"""')
    sep = "\n" + body_indent
    return sep.join(lines)


def _inject_docstrings(source: str, cm_entry: Dict[str, Any], log: logging.Logger) -> Tuple[str, int]:
    """Insert docstrings for undocumented symbols; returns (new_source, count_injected)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source, 0

    lines = source.splitlines(keepends=True)
    # collect (0-based insertion line, text) in reverse order to preserve positions
    insertions: List[Tuple[int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        # Skip if already documented
        if (node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)):
            continue

        sym = cm_entry["symbols"].get(node.name, {"type": "function", "args": [], "return_type": None})

        # Indentation of the def/class line + 4 spaces for body
        def_line    = lines[node.lineno - 1]
        body_indent = " " * (len(def_line) - len(def_line.lstrip()) + 4)

        doc_text   = _build_docstring(node.name, sym, body_indent)
        insert_txt = body_indent + doc_text + "\n"
        insert_at  = node.body[0].lineno - 1   # 0-based; insert before first body statement

        insertions.append((insert_at, insert_txt))
        log.debug(f"    + docstring → {node.name}() at body line {node.body[0].lineno}")

    if not insertions:
        return source, 0

    # Apply in reverse to keep line numbers stable
    insertions.sort(key=lambda x: x[0], reverse=True)
    for idx, txt in insertions:
        lines.insert(idx, txt)

    return "".join(lines), len(insertions)


def phase_inline_doc(state: WorkflowState, log: logging.Logger) -> None:
    """Generate and inject docstrings into all undocumented symbols; write patched files."""
    log.info("═══ Phase 3: Inline Doc Application ═══")
    patched: List[str] = []

    for file_entry in state.scope_manifest["files"]:
        if all(s["has_docstring"] for s in file_entry["symbols"]):
            log.debug(f"  {file_entry['path']} — fully documented, no changes needed")
            continue

        py_file = state.target_dir / file_entry["path"]
        source  = py_file.read_text(encoding="utf-8")
        cm_entry = state.code_map.get(file_entry["path"], {"symbols": {}})

        new_source, count = _inject_docstrings(source, cm_entry, log)
        if count > 0:
            py_file.write_text(new_source, encoding="utf-8")
            patched.append(file_entry["path"])
            log.info(f"  Patched: {file_entry['path']} ({count} docstring(s) added)")

    state.patched_files = patched
    log.info(f"  Total files patched: {len(patched)}")

    if not patched:
        log.info("  All symbols were already documented — no patches needed")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4 — SPHINX AUTOMATION & GENERATION
# Skill mapping: Skill 4 (Configuration Analysis), Skill 5 (Report Generation)
# ─────────────────────────────────────────────────────────────────────────────

_CONF_PY = """\
# Sphinx configuration — auto-generated by doc_workflow_runner.py
# Do not edit manually; regenerate by re-running the workflow.
project   = '{project}'
author    = 'Documentation Agent'
release   = '0.1'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]
html_theme = 'alabaster'
"""

def phase_sphinx_build(state: WorkflowState, log: logging.Logger) -> None:
    """Run sphinx-apidoc and sphinx-build; fall back to raw .rst generation if Sphinx absent."""
    log.info("═══ Phase 4: Sphinx Automation & Generation ═══")

    docs_dir  = state.output_dir / "docs"
    src_dir   = docs_dir / "source"
    build_dir = docs_dir / "build"
    for d in (src_dir, build_dir):
        d.mkdir(parents=True, exist_ok=True)

    project = state.target_dir.name

    # Write conf.py
    (src_dir / "conf.py").write_text(_CONF_PY.format(project=project), encoding="utf-8")
    log.debug(f"  conf.py → {src_dir / 'conf.py'}")

    # Try sphinx-apidoc
    apidoc = shutil.which("sphinx-apidoc")
    build  = shutil.which("sphinx-build")

    if apidoc:
        cmd = [apidoc, "-o", str(src_dir), str(state.target_dir), "--force", "--quiet"]
        log.info(f"  sphinx-apidoc: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            log.warning(f"  sphinx-apidoc exit={result.returncode}: {result.stderr.strip()[:300]}")
        else:
            log.info("  sphinx-apidoc completed successfully")
        state.sphinx_output += result.stdout + result.stderr
    else:
        log.info("  sphinx-apidoc not found — generating .rst files from scope manifest")
        modules: List[str] = []
        for fe in state.scope_manifest["files"]:
            mod = fe["path"].replace("\\", "/").removesuffix(".py").replace("/", ".")
            rst = (f"{mod}\n{'=' * len(mod)}\n\n"
                   f".. automodule:: {mod}\n"
                   f"   :members:\n   :undoc-members:\n   :show-inheritance:\n")
            (src_dir / f"{mod}.rst").write_text(rst, encoding="utf-8")
            modules.append(mod)
            log.debug(f"  Generated {mod}.rst")

        # modules.rst
        modules_rst = "modules\n=======\n\n.. toctree::\n   :maxdepth: 4\n\n"
        modules_rst += "".join(f"   {m}\n" for m in modules)
        (src_dir / "modules.rst").write_text(modules_rst, encoding="utf-8")

    # Write index.rst
    index = (f"{project}\n{'=' * len(project)}\n\n"
             ".. toctree::\n   :maxdepth: 2\n   :caption: Contents:\n\n   modules\n\n"
             "Indices and tables\n==================\n\n"
             "* :ref:`genindex`\n* :ref:`modindex`\n")
    (src_dir / "index.rst").write_text(index, encoding="utf-8")
    log.debug(f"  index.rst → {src_dir / 'index.rst'}")

    # Try sphinx-build
    if build:
        cmd = [build, "-b", "html", str(src_dir), str(build_dir), "-q"]
        log.info(f"  sphinx-build: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            log.warning(f"  sphinx-build exit={result.returncode}: {result.stderr.strip()[:500]}")
        else:
            log.info(f"  sphinx-build → {build_dir / 'index.html'}")
        state.sphinx_output += result.stdout + result.stderr
    else:
        msg = f"sphinx-build not found — .rst source ready at {src_dir}"
        log.info(f"  {msg}")
        state.sphinx_output += msg

    log.info(f"  Sphinx artifacts at: {docs_dir}")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 5 — REVIEW & MAINTENANCE
# Skill mapping: Skill 1 (Log & Evidence Parsing), Skill 5 (Report Generation)
# ─────────────────────────────────────────────────────────────────────────────

def phase_review(state: WorkflowState, log: logging.Logger) -> None:
    """Re-scan codebase; measure coverage delta; emit JSON maintenance report."""
    log.info("═══ Phase 5: Review & Maintenance ═══")

    new_total, new_undoc = 0, 0
    stale_files: List[str] = []

    for fe in state.scope_manifest["files"]:
        py_file = state.target_dir / fe["path"]
        source  = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue

        f_total, f_undoc = 0, 0
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            f_total  += 1
            new_total += 1
            has_doc = bool(
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            )
            if not has_doc:
                f_undoc  += 1
                new_undoc += 1
        if f_undoc > 0:
            stale_files.append(fe["path"])

    before = state.scope_manifest.get("initial_coverage_pct", 0.0)
    after  = round(100.0 * (new_total - new_undoc) / new_total, 1) if new_total else 0.0
    delta  = round(after - before, 1)

    report: Dict[str, Any] = {
        "generated_at":       datetime.datetime.utcnow().isoformat() + "Z",
        "coverage_before_pct": before,
        "coverage_after_pct":  after,
        "coverage_delta_pct":  delta,
        "total_symbols":       new_total,
        "remaining_undoc":     new_undoc,
        "patched_files":       state.patched_files,
        "stale_files":         stale_files,
        "workflow_errors":     state.errors,
    }
    state.coverage_report = report

    report_path = state.output_dir / "coverage_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    log.info(f"  Coverage : {before}% → {after}%  (Δ +{delta}%)")
    log.info(f"  Patched  : {len(state.patched_files)} file(s)")
    log.info(f"  Remaining undocumented: {new_undoc}")
    if stale_files:
        log.warning(f"  Still needs docs: {stale_files}")
    log.info(f"  Report   : {report_path}")


# ─────────────────────────────────────────────────────────────────────────────
# STATE MACHINE RUNNER
# ─────────────────────────────────────────────────────────────────────────────

PHASE_HANDLERS = {
    Phase.SCOPE_IDENTIFICATION: phase_scope_identification,
    Phase.FILE_ANALYSIS:        phase_file_analysis,
    Phase.INLINE_DOC:           phase_inline_doc,
    Phase.SPHINX_BUILD:         phase_sphinx_build,
    Phase.REVIEW:               phase_review,
}


def run_workflow(target_dir: Path, output_dir: Path) -> WorkflowState:
    """
    Execute the 5-phase documentation workflow as a linear state machine.

    Args:
        target_dir: Path to the Python codebase to document.
        output_dir: Directory where docs, logs and reports are written.

    Returns:
        WorkflowState: Final state with coverage_report, errors, and phase=DONE|FAILED.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "workflow.log"
    log      = setup_logging(log_path)

    state = WorkflowState(
        target_dir=target_dir.resolve(),
        output_dir=output_dir.resolve(),
        log_path=log_path,
    )

    banner = "=" * 62
    log.info(banner)
    log.info("  Documentation Workflow Runner — Starting")
    log.info(f"  Target : {state.target_dir}")
    log.info(f"  Output : {state.output_dir}")
    log.info(banner)

    while state.current_phase not in (Phase.DONE, Phase.FAILED):
        phase   = state.current_phase
        handler = PHASE_HANDLERS.get(phase)

        if handler is None:
            log.error(f"No handler registered for phase '{phase.value}' — aborting")
            state.current_phase = Phase.FAILED
            break

        try:
            handler(state, log)
            next_phase = TRANSITIONS.get(phase, Phase.DONE)
            log.info(f"  ✓ {phase.value} → {next_phase.value}\n")
            state.current_phase = next_phase

        except FileNotFoundError as exc:
            log.error(f"  ✗ {phase.value} FAILED — FileNotFoundError: {exc}")
            state.errors.append(f"{phase.value}: FileNotFoundError: {exc}")
            state.current_phase = Phase.FAILED

        except PermissionError as exc:
            log.error(f"  ✗ {phase.value} FAILED — PermissionError: {exc}")
            state.errors.append(f"{phase.value}: PermissionError: {exc}")
            state.current_phase = Phase.FAILED

        except Exception as exc:
            log.exception(f"  ✗ {phase.value} FAILED — {type(exc).__name__}: {exc}")
            state.errors.append(f"{phase.value}: {type(exc).__name__}: {exc}")
            state.current_phase = Phase.FAILED

    if state.current_phase == Phase.DONE:
        r = state.coverage_report
        log.info(banner)
        log.info("  Workflow COMPLETE")
        log.info(f"  Doc coverage : {r.get('coverage_before_pct','?')}% → {r.get('coverage_after_pct','?')}%")
        log.info(f"  Files patched: {len(state.patched_files)}")
        log.info(f"  Log          : {log_path}")
        log.info(banner)
    else:
        log.error(f"Workflow FAILED at phase: {state.current_phase.value}")
        for err in state.errors:
            log.error(f"  {err}")

    return state


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Documentation Workflow Runner — 5-phase state machine"
    )
    parser.add_argument(
        "target_dir",
        help="Path to the Python codebase to document"
    )
    parser.add_argument(
        "--output", "-o",
        default="./doc_output",
        help="Output directory for docs, logs and reports (default: ./doc_output)"
    )
    args = parser.parse_args()

    final = run_workflow(Path(args.target_dir), Path(args.output))
    sys.exit(0 if final.current_phase == Phase.DONE else 1)
