# Agents

Five specialist agents that compose the engineering investigation workflow. Each
agent is bounded (explicit out-of-scope list, budgets, stop conditions), reviewable
(fixed output contract + review checklist), and reuses the shared skills in
[../skills/](../skills/SKILL.md).

VS Code discovers these automatically from `.github/agents/*.agent.md`.

| Agent | File | Deliverable | Entry gate |
|---|---|---|---|
| Requirements Agent | [requirements-agent.agent.md](requirements-agent.agent.md) | `IRB` + traceability matrix | Any new request |
| Debugging Agent | [debugging-agent.agent.md](debugging-agent.agent.md) | `IR` investigation report | `IRB` status `READY` |
| Feature Agent | [feature-agent.agent.md](feature-agent.agent.md) | `FP` feature proposal | `IRB` with acceptance criteria |
| Refactoring Agent | [refactoring-agent.agent.md](refactoring-agent.agent.md) | `RFP` refactoring plan & record | Green baseline + tests exist |
| Documentation Agent | [documentation-agent.agent.md](documentation-agent.agent.md) | `DOC` engineering document | A pinned revision |

## Agent x Skill matrix

Numbers show the order in which each agent invokes the skill (`\u2013` = not used).

| Skill | Requirements | Debugging | Feature | Refactoring | Documentation |
|---|---|---|---|---|---|
| [1 — Log & Evidence Parsing](../skills/skill-1-log-evidence-parsing.md) | 2 | 1 | 4 | 3 | 4 |
| [2 — Code Search & Context Retrieval](../skills/skill-2-code-search-context-retrieval.md) | 3 | 4 | 2 | 1 | 2 |
| [3 — Historical Pattern Lookup](../skills/skill-3-historical-pattern-lookup.md) | 1 | 2 | 1 | 2 | 1 |
| [4 — Configuration Analysis](../skills/skill-4-configuration-analysis.md) | 4 | 3 | 3 | 4 | 3 |
| [5 — Structured Report Generation](../skills/skill-5-structured-report-generation.md) | 5 | 5 | 5 | 5 | 5 |

Two cross-cutting skills are available to every agent:

- [requirement.md](../skills/requirement.md) — investigation requirement gathering (`IRB`)
- [rollback-and-recovery.md](../skills/rollback-and-recovery.md) — checkpoint, revert, attempt budgets (`RER`)

Full index: [../skills/SKILL.md](../skills/SKILL.md)

## Artifact flow

Skills emit typed artifacts; agents consume them and emit a single reviewable deliverable.

```mermaid
flowchart LR
  subgraph Skills
    S1[Skill 1<br/>EVS]
    S2[Skill 2<br/>CTX]
    S3[Skill 3<br/>PAR]
    S4[Skill 4<br/>CDR]
    S5[Skill 5<br/>report]
  end

  REQ[Requirements Agent] -->|IRB READY| DBG[Debugging Agent]
  REQ -->|IRB + criteria| FEA[Feature Agent]
  DBG -->|structural blocker| REF[Refactoring Agent]
  FEA -->|structural blocker| REF
  DBG -->|root cause| DOC[Documentation Agent]
  FEA -->|shipped| DOC
  REF -->|bug exposed| DBG
  DOC -->|DOC_DRIFT| REQ

  S1 --> REQ & DBG & FEA & REF & DOC
  S2 --> REQ & DBG & FEA & REF & DOC
  S3 --> REQ & DBG & FEA & REF & DOC
  S4 --> REQ & DBG & FEA & REF & DOC
  S5 --> REQ & DBG & FEA & REF & DOC
```

## Artifact IDs

| ID | Artifact | Produced by |
|---|---|---|
| `EVS-*` | Evidence Set | Skill 1 |
| `CTX-*` | Context Pack | Skill 2 |
| `PAR-*` | Prior-Art Report | Skill 3 |
| `CDR-*` | Configuration Delta Report | Skill 4 |
| `IRB-*` | Investigation Requirement Brief | Requirements Agent |
| `IR-*` | Investigation Report | Debugging Agent |
| `FP-*` | Feature Proposal | Feature Agent |
| `RFP-*` | Refactoring Plan & Record | Refactoring Agent |
| `DOC-*` | Engineering Document | Documentation Agent |
| `RER-*` | Recovery Execution Record | Rollback & Recovery skill |

## Shared invariants

Every agent in this folder obeys the same rules:

1. **Bounded** \u2014 explicit in/out of scope, question budget, change budget, and a terminal `BLOCKED` / `NOT_SAFE` state.
2. **Evidence-first** \u2014 no claim without a citation (`path#Lstart-Lend @ SHA`, run ID, ticket ID or doc section).
3. **Reversible** \u2014 checkpoint before edits; every change has a written revert step.
4. **Reviewable** \u2014 one fixed-schema deliverable plus a review checklist a peer can run.
5. **Handoff, don't sprawl** \u2014 work outside an agent's scope is handed to the owning agent, never absorbed.

## Using these with VS Code

VS Code discovers custom agents from `.github/agents/*.agent.md` and skills from
`.github/skills/`. Both folders are already in their discoverable locations, so no
copying is required. Every skill file carries YAML frontmatter (`name`,
`description`); see [../skills/SKILL.md](../skills/SKILL.md) for the full index.
