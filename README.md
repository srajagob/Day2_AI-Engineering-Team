# Day2_AI-Engineering-Team

An engineering workflow built from **5 specialist agents** and **5 reusable skills**.
Each unit is *reusable* (composable across domains), *reviewable* (fixed output
contract + checklist) and *bounded* (explicit out-of-scope list, budgets, stop
conditions).

## Layout

```
AGENTS/                          5 specialist agents (one sub-folder each)
  requirements-agent/            intake, IRB, traceability
  debugging-agent/               failure -> evidence-backed root cause
  feature-agent/                 capability request -> feature proposal
  refactoring-agent/             behaviour-preserving structure changes
  documentation-agent/           verified engineering documentation
  README.md                      agent x skill matrix and artifact flow
SKILLS/                          shared capabilities used by all agents
  skill-1-log-evidence-parsing.md
  skill-2-code-search-context-retrieval.md
  skill-3-historical-pattern-lookup.md
  skill-4-configuration-analysis.md
  skill-5-structured-report-generation.md
  requirement.md                 investigation requirement gathering (IRB)
  rollback-and-recovery.md       checkpoint / revert / attempt budgets (RER)
```

Start with [AGENTS/README.md](AGENTS/README.md) for the agent x skill matrix,
artifact flow and shared invariants.