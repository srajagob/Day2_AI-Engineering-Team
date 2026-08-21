# Skill 1: Log & Evidence Parsing

**Responsibility:** Extract structured signals from raw engineering inputs.

**Inputs:**
- Logs
- Error messages
- Test results
- Validation results

**What it does:**
- Parses structured and unstructured log formats
- Extracts stack traces, error codes, failure signatures, and timestamps
- Normalises test result statuses (pass/fail/skip) into a queryable format

**Used by:**
| Agent | Purpose |
|---|---|
| Feature Agent | Understand current system behavior before adding a feature |
| Debugging Agent | Find failure signatures and error patterns |
| Documentation Agent | Capture findings and failure evidence in written form |
| Refactoring Agent | Spot code quality issues surfaced in runtime logs |
| Requirements Agent | Trace failures and validation results back to requirements |
