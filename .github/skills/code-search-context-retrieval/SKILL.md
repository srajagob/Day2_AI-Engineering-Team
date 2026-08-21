# Skill 2: Code Search & Context Retrieval

**Responsibility:** Navigate and retrieve relevant context from source code.

**Inputs:**
- Source code

**What it does:**
- Locates functions, classes, and modules relevant to a query
- Retrieves surrounding code context (callers, callees, dependencies)
- Identifies recent changes or annotated regions

**Used by:**
| Agent | Purpose |
|---|---|
| Feature Agent | Locate where to add or extend a feature |
| Debugging Agent | Pinpoint the bug location in code |
| Documentation Agent | Know exactly what code to describe |
| Refactoring Agent | Find refactor candidates and their scope |
| Requirements Agent | Verify whether code implements a stated requirement |
