"""
test_result_analyzer.py — EDA regression test result analysis utilities.

Parses NBJOBS / regression XML/CSV result tables, computes pass/fail statistics,
and correlates failures with known error signatures for root-cause triage.

NOTE: Several functions are intentionally undocumented to demonstrate Phase 3
      (Inline Doc Application) of the Documentation Agent workflow.
"""

import csv
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TestResult:
    """Represents a single test case result from a regression run."""

    name:        str
    status:      str          # PASS | FAIL | SKIP | ERROR
    duration_s:  float        = 0.0
    error_code:  Optional[str] = None
    log_path:    Optional[str] = None
    tags:        List[str]    = field(default_factory=list)

    def passed(self) -> bool:
        """Return True if the test passed."""
        return self.status.upper() == "PASS"

    def failed(self) -> bool:
        """
        Failed.
        
        Returns:
            bool: TODO — describe return value.
        
        Raises:
            TODO — list exceptions this function may raise.
        """
        return self.status.upper() in ("FAIL", "ERROR")


@dataclass
class RegressionRun:
    """
    Regressionrun.
    
    Attributes:
        TODO — list public attributes.
    """
    name:    str
    results: List[TestResult] = field(default_factory=list)

    def pass_rate(self) -> float:
        """
        Pass rate.
        
        Returns:
            float: TODO — describe return value.
        
        Raises:
            TODO — list exceptions this function may raise.
        """
        if not self.results:
            return 0.0
        passed = sum(1 for r in self.results if r.passed())
        return round(100.0 * passed / len(self.results), 2)

    def failures(self) -> List[TestResult]:
        """
        Failures.
        
        Returns:
            List[TestResult]: TODO — describe return value.
        
        Raises:
            TODO — list exceptions this function may raise.
        """
        return [r for r in self.results if r.failed()]


# ─────────────────────────────────────────────────────────────────────────────
# PARSERS (intentionally undocumented)
# ─────────────────────────────────────────────────────────────────────────────

def parse_csv_results(filepath: str) -> RegressionRun:
    """
    Parse csv results.
    
    Args:
        filepath: TODO — describe parameter.
    
    Returns:
        RegressionRun: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    run = RegressionRun(name=filepath)
    with open(filepath, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            result = TestResult(
                name=row.get("test_name", "unknown"),
                status=row.get("status", "UNKNOWN"),
                duration_s=float(row.get("duration_s", 0.0)),
                error_code=row.get("error_code") or None,
                log_path=row.get("log_path") or None,
                tags=row.get("tags", "").split(",") if row.get("tags") else [],
            )
            run.results.append(result)
    return run


def parse_json_results(filepath: str) -> RegressionRun:
    """
    Parse json results.
    
    Args:
        filepath: TODO — describe parameter.
    
    Returns:
        RegressionRun: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    with open(filepath, encoding="utf-8") as fh:
        data = json.load(fh)
    run = RegressionRun(name=data.get("run_name", filepath))
    for item in data.get("results", []):
        result = TestResult(
            name=item["test_name"],
            status=item.get("status", "UNKNOWN"),
            duration_s=float(item.get("duration_s", 0.0)),
            error_code=item.get("error_code"),
            log_path=item.get("log_path"),
            tags=item.get("tags", []),
        )
        run.results.append(result)
    return run


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS FUNCTIONS (intentionally undocumented)
# ─────────────────────────────────────────────────────────────────────────────

def group_failures_by_error_code(run: RegressionRun) -> Dict[str, List[TestResult]]:
    """
    Group failures by error code.
    
    Args:
        run: TODO — describe parameter.
    
    Returns:
        Dict[str, List[TestResult]]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    groups: Dict[str, List[TestResult]] = {}
    for r in run.failures():
        key = r.error_code or "NO_CODE"
        groups.setdefault(key, []).append(r)
    return groups


def top_failure_codes(run: RegressionRun, n: int = 5) -> List[Tuple[str, int]]:
    """
    Top failure codes.
    
    Args:
        run: TODO — describe parameter.
        n: TODO — describe parameter.
    
    Returns:
        List[Tuple[str, int]]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    groups = group_failures_by_error_code(run)
    ranked = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)
    return [(code, len(results)) for code, results in ranked[:n]]


def compare_runs(baseline: RegressionRun, current: RegressionRun) -> Dict[str, List[str]]:
    """
    Compare runs.
    
    Args:
        baseline: TODO — describe parameter.
        current: TODO — describe parameter.
    
    Returns:
        Dict[str, List[str]]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    baseline_pass = {r.name for r in baseline.results if r.passed()}
    current_pass  = {r.name for r in current.results  if r.passed()}
    return {
        "regressions":  sorted(baseline_pass - current_pass),
        "fixes":        sorted(current_pass - baseline_pass),
        "stable_pass":  sorted(baseline_pass & current_pass),
    }


def slowest_tests(run: RegressionRun, n: int = 10) -> List[TestResult]:
    """
    Slowest tests.
    
    Args:
        run: TODO — describe parameter.
        n: TODO — describe parameter.
    
    Returns:
        List[TestResult]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    return sorted(run.results, key=lambda r: r.duration_s, reverse=True)[:n]


def filter_by_tag(run: RegressionRun, tag: str) -> List[TestResult]:
    """
    Filter by tag.
    
    Args:
        run: TODO — describe parameter.
        tag: TODO — describe parameter.
    
    Returns:
        List[TestResult]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    return [r for r in run.results if tag in r.tags]


def build_summary_report(run: RegressionRun) -> Dict:
    """
    Build summary report.
    
    Args:
        run: TODO — describe parameter.
    
    Returns:
        Dict: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    top = top_failure_codes(run)
    return {
        "run_name":       run.name,
        "total":          len(run.results),
        "pass_rate_pct":  run.pass_rate(),
        "failures":       len(run.failures()),
        "top_error_codes": [{"code": c, "count": n} for c, n in top],
    }
