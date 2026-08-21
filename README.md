# Day2_AI-Engineering-Team

An engineering workflow built from **5 specialist agents** and **5 reusable skills**.
Each unit is *reusable* (composable across domains), *reviewable* (fixed output
contract + checklist) and *bounded* (explicit out-of-scope list, budgets, stop
conditions).

## Layout

```
.github/
  agents/                        5 specialist agents (auto-discovered by VS Code)
    requirements-agent.agent.md  intake, IRB, traceability
    debugging-agent.agent.md     failure -> evidence-backed root cause
    feature-agent.agent.md       capability request -> feature proposal
    refactoring-agent.agent.md   behaviour-preserving structure changes
    documentation-agent.agent.md verified engineering documentation
    README.md                    agent x skill matrix and artifact flow
  skills/                        shared capabilities used by all agents
    SKILL.md                     index of every skill + selection guide
    skill-1-log-evidence-parsing.md
    skill-2-code-search-context-retrieval.md
    skill-3-historical-pattern-lookup.md
    skill-4-configuration-analysis.md
    skill-5-structured-report-generation.md
    requirement.md               investigation requirement gathering (IRB)
    rollback-and-recovery.md     checkpoint / revert / attempt budgets (RER)
```

Start with [.github/agents/README.md](.github/agents/README.md) for the agent x skill
matrix, artifact flow and shared invariants, or
[.github/skills/SKILL.md](.github/skills/SKILL.md) for the skill index.