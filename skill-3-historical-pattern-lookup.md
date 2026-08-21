# Skill 3: Historical Pattern Lookup

**Responsibility:** Search past records for matching or similar patterns.

**Inputs:**
- Historical failures
- Test cases
- Engineering documentation

**What it does:**
- Searches historical failure records for similar error signatures
- Retrieves previously written test cases relevant to a scenario
- Surfaces related engineering documentation or past decisions

**Used by:**
| Agent | Purpose |
|---|---|
| Feature Agent | Avoid re-implementing something previously attempted |
| Debugging Agent | Match current failure against known issues |
| Documentation Agent | Reference and link to prior documentation |
| Refactoring Agent | Identify code that has been refactored or reverted before |
| Requirements Agent | Compare current requirements against historical versions |
