"""
log_parser.py — EDA tool log parsing utilities.

Parses Fusion Compiler, PrimeTime and VCS log files into structured LogEntry
objects for downstream error correlation and root-cause analysis.

NOTE: Some functions below are intentionally undocumented to demonstrate the
      Documentation Agent workflow (Phase 3: Inline Doc Application).
"""

import re
from datetime import datetime
from typing import List, Optional, Dict


# ─────────────────────────────────────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────────────────────────────────────

class LogEntry:
    """Represents a single parsed line from an EDA tool log file."""

    def __init__(
        self,
        timestamp: Optional[datetime],
        level: str,
        tool: str,
        code: str,
        message: str,
        line_number: int,
    ) -> None:
        """
          init  .
        
        Args:
            timestamp: TODO — describe parameter.
            level: TODO — describe parameter.
            tool: TODO — describe parameter.
            code: TODO — describe parameter.
            message: TODO — describe parameter.
            line_number: TODO — describe parameter.
        
        Raises:
            TODO — list exceptions this function may raise.
        """
        self.timestamp   = timestamp
        self.level       = level.upper()     # ERROR | WARNING | INFO
        self.tool        = tool
        self.code        = code              # e.g. CTS-018, MV-016
        self.message     = message
        self.line_number = line_number

    def is_error(self) -> bool:
        """Return True if this entry represents an error-level message."""
        return self.level == "ERROR"

    def is_warning(self) -> bool:
        """
        Is warning.
        
        Returns:
            bool: TODO — describe return value.
        
        Raises:
            TODO — list exceptions this function may raise.
        """
        return self.level == "WARNING"

    def __repr__(self) -> str:
        """
          repr  .
        
        Returns:
            str: TODO — describe return value.
        
        Raises:
            TODO — list exceptions this function may raise.
        """
        return f"<LogEntry [{self.level}] {self.tool}:{self.code} line={self.line_number}>"


# ─────────────────────────────────────────────────────────────────────────────
# PARSING  (intentionally undocumented — workflow will inject docstrings here)
# ─────────────────────────────────────────────────────────────────────────────

# Pattern: "Error: CTS-018: message text"  or  "Warning: MV-016: message"
_LOG_PATTERN = re.compile(
    r"^(?P<level>Error|Warning|Info|Note):\s+"
    r"(?P<code>[A-Z0-9_]+-\d+)?:?\s*"
    r"(?P<message>.+)$",
    re.IGNORECASE,
)

_TIMESTAMP_PATTERN = re.compile(
    r"^\[(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\]"
)


def _parse_timestamp(line: str) -> Optional[datetime]:
    """
     parse timestamp.
    
    Args:
        line: TODO — describe parameter.
    
    Returns:
        Optional[datetime]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    m = _TIMESTAMP_PATTERN.match(line)
    if m:
        try:
            return datetime.fromisoformat(m.group("ts"))
        except ValueError:
            return None
    return None


def _detect_tool(filepath: str) -> str:
    """
     detect tool.
    
    Args:
        filepath: TODO — describe parameter.
    
    Returns:
        str: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    lower = filepath.lower()
    if "fc_shell" in lower or "fusion" in lower:
        return "FC"
    if "pt_shell" in lower or "primetime" in lower:
        return "PT"
    if "vcs" in lower:
        return "VCS"
    if "spyglass" in lower:
        return "SpyGlass"
    return "UNKNOWN"


def parse_eda_log(filepath: str) -> List[LogEntry]:
    """
    Parse eda log.
    
    Args:
        filepath: TODO — describe parameter.
    
    Returns:
        List[LogEntry]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    tool    = _detect_tool(filepath)
    entries = []
    with open(filepath, encoding="utf-8", errors="replace") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            ts   = _parse_timestamp(line)
            m    = _LOG_PATTERN.search(line)
            if m:
                entry = LogEntry(
                    timestamp=ts,
                    level=m.group("level"),
                    tool=tool,
                    code=m.group("code") or "",
                    message=m.group("message").strip(),
                    line_number=lineno,
                )
                entries.append(entry)
    return entries


def extract_errors(entries: List[LogEntry]) -> List[LogEntry]:
    """
    Extract errors.
    
    Args:
        entries: TODO — describe parameter.
    
    Returns:
        List[LogEntry]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    return [e for e in entries if e.is_error()]


def extract_warnings(entries: List[LogEntry]) -> List[LogEntry]:
    """
    Extract warnings.
    
    Args:
        entries: TODO — describe parameter.
    
    Returns:
        List[LogEntry]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    return [e for e in entries if e.is_warning()]


def group_by_code(entries: List[LogEntry]) -> Dict[str, List[LogEntry]]:
    """
    Group by code.
    
    Args:
        entries: TODO — describe parameter.
    
    Returns:
        Dict[str, List[LogEntry]]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    groups: Dict[str, List[LogEntry]] = {}
    for e in entries:
        groups.setdefault(e.code or "NO_CODE", []).append(e)
    return groups


def top_error_codes(entries: List[LogEntry], n: int = 10) -> List[tuple]:
    """
    Top error codes.
    
    Args:
        entries: TODO — describe parameter.
        n: TODO — describe parameter.
    
    Returns:
        List[tuple]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    groups = group_by_code(extract_errors(entries))
    ranked = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)
    return ranked[:n]


def filter_by_stage(entries: List[LogEntry], stage_keyword: str) -> List[LogEntry]:
    """
    Filter by stage.
    
    Args:
        entries: TODO — describe parameter.
        stage_keyword: TODO — describe parameter.
    
    Returns:
        List[LogEntry]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    kw = stage_keyword.lower()
    return [e for e in entries if kw in e.message.lower()]


def summarise(entries: List[LogEntry]) -> Dict[str, int]:
    """
    Summarise.
    
    Args:
        entries: TODO — describe parameter.
    
    Returns:
        Dict[str, int]: TODO — describe return value.
    
    Raises:
        TODO — list exceptions this function may raise.
    """
    return {
        "total":    len(entries),
        "errors":   sum(1 for e in entries if e.is_error()),
        "warnings": sum(1 for e in entries if e.is_warning()),
        "infos":    sum(1 for e in entries if e.level == "INFO"),
    }
