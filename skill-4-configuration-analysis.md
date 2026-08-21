# Skill 4: Configuration Analysis

**Responsibility:** Parse, diff, and validate configuration state.

**Inputs:**
- Configuration files

**What it does:**
- Parses configuration files into structured key-value representations
- Diffs two configurations to highlight changes
- Flags values that deviate from a baseline or expected state

**Used by:**
| Agent | Purpose |
|---|---|
| Feature Agent | Validate that required configuration exists for a new feature |
| Debugging Agent | Identify configuration mismatches as a root cause |
| Documentation Agent | Document the configuration state at a point in time |
| Refactoring Agent | Flag configuration-driven complexity in code |
| Requirements Agent | Verify that configuration satisfies defined requirements |
