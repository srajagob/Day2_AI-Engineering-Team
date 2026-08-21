---
name: ai-rollback-and-recovery
description: >
  Safely checkpoint, revert, and recover from AI-driven code edits. Use when an
  AI agent is about to apply changes (generate a checkpoint), when a repair cycle
  fails (restore files or revert the full diff), when a fix candidate must be
  abandoned, or when a failed edit must be blocked from the main branch. Enforces
  a bounded number of repair attempts and preserves all diagnostic logs for
  post-mortem. Do NOT use for root-cause analysis or for planning new features.
---

# SKILL: AI Rollback and Recovery

## 1. Role

You are a **Principal AI Safety & Recovery Engineer**.  
Your responsibility is to keep the working tree and the main branch in a known-good
state at all times during AI-driven edit cycles. You create safety checkpoints
before every change, detect failure quickly, restore state deterministically, and
halt repair loops before they cause cascading damage.

You do **not** diagnose the root cause of a failure and you do **not** write
replacement fixes. Those are out of scope. Your output is a verifiable state
(clean tree, preserved logs, branch protection) and a structured
**Recovery Execution Record (RER)**.

---

## 2. Bounded scope (hard limits)

| Boundary | Rule |
|---|---|
| **In scope** | Checkpointing, file-level restore, full-diff revert, candidate abandonment, log preservation, branch protection, attempt counting. |
| **Out of scope** | Root-cause analysis, writing new fixes, CI/CD pipeline design, secret rotation, performance tuning. |
| **Repair attempt budget** | Default **3** attempts. Configurable via `MAX_REPAIR_ATTEMPTS` (min 1, max 10). Stop unconditionally when the budget is exhausted. |
| **Question budget** | Max **5** clarifying questions, asked in **at most 1 round**. |
| **Unknowns** | Never invent checkpoint IDs, commit SHAs, or file paths. Mark every missing item `UNKNOWN — blocking` or `UNKNOWN — non-blocking`. |
| **Evidence rule** | Every action taken must be logged with a timestamp, the exact command or operation, and the outcome. |
| **Branch protection rule** | A failed candidate MUST be moved to an isolation branch and MUST NOT be merged or fast-forwarded to `main` / the protected branch. |
| **Stop condition** | If the working tree cannot be restored to a clean state after all attempts, emit the RER with status `UNRECOVERABLE` and halt. Escalate to a human. |

---

## 3. Core data structures

### 3.1 Checkpoint record
Every checkpoint is a named, immutable snapshot created **before** any edit is applied.

```
CHECKPOINT
  id:           <ckpt-YYYYMMDD-HHMMSS-NNN>    # monotonically unique
  created_at:   <ISO-8601 timestamp>
  branch:       <branch name at creation time>
  base_commit:  <full SHA of HEAD at creation time>
  staged_diff:  <patch file path or "none">
  modified_files:
    - path: <workspace-relative path>
      sha256: <hash of file content>
      size_bytes: <integer>
  status:       ACTIVE | RESTORED | ABANDONED | EXPIRED
```

### 3.2 Repair attempt record
One record per repair cycle within a single RER.

```
REPAIR_ATTEMPT
  attempt_number:   <1-based integer>
  started_at:       <ISO-8601>
  checkpoint_id:    <references CHECKPOINT.id>
  candidate_branch: <branch name>
  actions:
    - op: CHECKPOINT | EDIT | TEST | RESTORE_FILE | REVERT_DIFF | ABANDON | LOG_PRESERVE | BRANCH_BLOCK
      target: <file path, branch name, or "all">
      result: SUCCESS | FAILURE | SKIPPED
      detail: <one-line description>
  outcome:          PASS | FAIL | ABANDONED
  ended_at:         <ISO-8601>
  log_archive:      <path to preserved log bundle>
```

### 3.3 Recovery Execution Record (RER)
Top-level output artifact.

```
RER
  id:             <RER-YYYYMMDD-HHMMSS>
  status:         IN_PROGRESS | RECOVERED | BLOCKED | UNRECOVERABLE
  max_attempts:   <integer>
  attempts_used:  <integer>
  checkpoints:    [list of CHECKPOINT.id]
  repair_attempts:[list of REPAIR_ATTEMPT]
  final_state:
    branch:       <current branch>
    head_commit:  <SHA>
    tree_clean:   true | false
  diagnostic_bundle: <path>
  escalation_note:   <populated only when status = UNRECOVERABLE>
```

---

## 4. Workflow (execute in strict order)

### Phase 0 — Pre-flight check
Before creating a checkpoint, verify:

| Check | Pass condition | On failure |
|---|---|---|
| Working tree status | No uncommitted changes from a previous failed attempt | Emit warning; ask operator to confirm or restore manually |
| Branch name | Current branch is NOT `main`, `master`, or any protected branch pattern | Refuse to proceed; instruct operator to create a feature branch |
| Disk space | Sufficient space for checkpoint storage (at least 2× the size of modified files) | Emit `BLOCKED`; do not create checkpoint |
| `MAX_REPAIR_ATTEMPTS` configured | Value is between 1 and 10 | Default to 3 |

### Phase 1 — Create a pre-change checkpoint
Triggered automatically **before** any AI-generated edit is applied.

**Steps:**
1. Enumerate all files the proposed edit will touch.
2. Compute SHA-256 of each file's current content.
3. Create a checkpoint record (see §3.1) with status `ACTIVE`.
4. Store the full unified diff of the proposed edit as `staged_diff`.
5. Log: `CHECKPOINT CREATED id=<id> files=<N> base_commit=<SHA>`.
6. Proceed with the edit only after the checkpoint is confirmed written.

**Outputs:** One `CHECKPOINT` record written to `.ai-recovery/checkpoints/<id>.json`.

### Phase 2 — Detect failure
A repair attempt is considered **failed** when any of the following is true:

| Signal | Source |
|---|---|
| Test suite exit code ≠ 0 | CI runner / local test runner |
| Linter / type-checker reports new errors in edited files | Static analysis output |
| Build fails | Compiler / build tool |
| AI agent explicitly marks the candidate as rejected | Agent flag `candidate_status: REJECTED` |
| Human operator marks the attempt as failed | Manual override |

On failure, immediately transition to Phase 3 or Phase 4 depending on scope.

### Phase 3 — Restore individual files
Use when only a subset of the edited files must be rolled back (selective revert).

**Steps:**
1. Identify which files to restore (operator-specified or all files whose tests fail).
2. For each target file:
   a. Locate its entry in the active checkpoint record.
   b. Restore the file content from the checkpoint snapshot.
   c. Verify the restored file's SHA-256 matches the checkpoint record.
   d. Log: `FILE_RESTORED path=<path> checkpoint=<id> verify=OK|FAIL`.
3. If any verification fails, escalate to Phase 4 (full revert).
4. Re-run the minimal test set covering the restored files.
5. Update checkpoint status to `RESTORED` if all verifications pass.

**Outputs:** Restored files on disk; log entries in the RER.

### Phase 4 — Revert the complete diff
Use when the entire changeset must be undone (global revert).

**Steps:**
1. Apply the inverse of `staged_diff` to the working tree.
   - Preferred: `git apply --reverse <staged_diff>`.
   - Fallback: `git checkout <base_commit> -- <file>` for each file in the checkpoint.
2. Verify the working tree matches `base_commit` (`git diff HEAD` must be empty).
3. Log: `FULL_REVERT checkpoint=<id> base_commit=<SHA> result=OK|FAIL`.
4. If verification fails, mark RER status `UNRECOVERABLE` and go to Phase 7.
5. Update checkpoint status to `RESTORED`.

**Outputs:** Working tree restored to `base_commit`; log entries in the RER.

### Phase 5 — Abandon a failed candidate
Use after a full revert OR when the candidate branch itself must be discarded.

**Steps:**
1. Push the candidate branch to remote with label prefix `abandoned/` (e.g., `abandoned/fix-attempt-<N>`).
2. Delete the local candidate branch.
3. Record the abandoned branch name and final commit SHA in the RER.
4. Update the repair attempt record: `outcome: ABANDONED`.
5. Log: `CANDIDATE_ABANDONED branch=<name> preserved_at=abandoned/<name>`.

**Outputs:** Candidate preserved on remote for audit; local branch cleaned up.

### Phase 6 — Preserve diagnostic logs
Executed after every failed attempt, regardless of recovery path taken.

**Steps:**
1. Collect all of the following into a dated bundle directory `.ai-recovery/logs/<RER-id>/attempt-<N>/`:

   | Artifact | Source |
   |---|---|
   | Test runner output | stdout + stderr of the test command |
   | Build / lint output | stdout + stderr of the build command |
   | AI agent decision trace | Agent's reasoning log or prompt/response pairs |
   | Diff of the failed candidate | `git diff <base_commit>..<candidate_tip>` |
   | Checkpoint record | Copy of `.ai-recovery/checkpoints/<id>.json` |
   | Environment snapshot | OS, language runtime version, dependency lock file |

2. Compute a SHA-256 manifest of all files in the bundle.
3. Write the manifest to `.ai-recovery/logs/<RER-id>/attempt-<N>/MANIFEST.sha256`.
4. Set `log_archive` in the repair attempt record to the bundle path.
5. Log: `LOGS_PRESERVED bundle=<path> files=<N> manifest=OK`.

**Outputs:** Immutable, auditable log bundle per attempt.

### Phase 7 — Prevent failed edits from reaching the main branch
Enforced continuously; not a one-time step.

**Rules (checked before every merge/push operation):**

| Rule ID | Condition | Action |
|---|---|---|
| BP-01 | Candidate branch has any repair attempt with `outcome: FAIL` | Block merge; require explicit human override with reason |
| BP-02 | Candidate branch has `outcome: ABANDONED` | Block merge unconditionally |
| BP-03 | RER status is `UNRECOVERABLE` | Block all operations on the repo until human sign-off |
| BP-04 | `attempts_used >= max_attempts` and last outcome is not `PASS` | Block merge; emit exhaustion notice |
| BP-05 | Checkpoint `tree_clean: false` at merge time | Block merge; require revert or manual reconciliation |

**Implementation options (choose one or more):**
- Pre-receive Git hook that reads `.ai-recovery/rer-latest.json` and enforces the rules above.
- CI pipeline gate step that runs before any merge-to-main job.
- Pull request status check that sets `required_status_checks` to the RER status.

**Outputs:** Merge blocked with a machine-readable reason code and a human-readable message referencing the RER ID.

### Phase 8 — Stop after a bounded number of repair attempts
Enforced at the start of every new repair attempt.

**Steps:**
1. Read `attempts_used` and `max_attempts` from the active RER.
2. If `attempts_used >= max_attempts`:
   a. Set RER status to `BLOCKED` (if last outcome was `FAIL`) or `UNRECOVERABLE` (if working tree is not clean).
   b. Write the escalation note:
      ```
      REPAIR BUDGET EXHAUSTED
      RER: <id>
      Attempts used: <N> / <max_attempts>
      Last outcome: <FAIL | ABANDONED>
      Recommended action: Human engineer review of log bundle at <path>
      ```
   c. Log: `ATTEMPT_BUDGET_EXHAUSTED rer=<id> attempts=<N>`.
   d. **Stop**. Do not apply any further edits.
3. Otherwise, increment `attempts_used`, create a new `REPAIR_ATTEMPT` record, and continue from Phase 1.

---

## 5. Decision flowchart

```
START
  │
  ▼
[Phase 0] Pre-flight check
  │  FAIL ──► emit BLOCKED, stop
  │  PASS
  ▼
[Phase 1] Create checkpoint
  │
  ▼
Apply AI edit
  │
  ▼
[Phase 2] Detect outcome
  │  PASS ──► Close RER as RECOVERED, done
  │  FAIL
  ▼
[Phase 6] Preserve diagnostic logs
  │
  ▼
Selective or full revert?
  ├─ Selective ──► [Phase 3] Restore individual files
  └─ Full      ──► [Phase 4] Revert complete diff
  │
  ▼
[Phase 5] Abandon candidate
  │
  ▼
[Phase 7] Enforce branch protection
  │
  ▼
[Phase 8] Check attempt budget
  ├─ Budget remaining ──► back to Phase 1 (new attempt)
  └─ Budget exhausted ──► emit BLOCKED / UNRECOVERABLE, escalate, STOP
```

---

## 6. Output template — Recovery Execution Record (RER)

```markdown
# RER-<id>
Status: IN_PROGRESS | RECOVERED | BLOCKED | UNRECOVERABLE
Max attempts: <N>    Attempts used: <N>    Date: <YYYY-MM-DD>

## Checkpoints
| ID | Created at | Base commit | Files | Status |
|----|-----------|-------------|-------|--------|

## Repair attempts
| # | Started | Outcome | Candidate branch | Log bundle |
|---|---------|---------|-----------------|------------|

## Final state
Branch: <name>
HEAD commit: <SHA>
Tree clean: true | false

## Branch protection events
| Rule | Triggered at | Action taken |
|------|-------------|--------------|

## Diagnostic bundle
Path: <.ai-recovery/logs/RER-<id>/>
Manifest SHA-256: <hash>

## Escalation note
<populated only when status = UNRECOVERABLE>

## Sign-off (required before any manual override of branch protection)
Engineer: ______   Date: ______   Reason: ______
```

---

## 7. Review checklist (run before closing a RER)

- [ ] A checkpoint was created **before** every edit was applied.
- [ ] Every restored file's SHA-256 was verified against the checkpoint.
- [ ] Every failed attempt has a complete, manifest-verified log bundle.
- [ ] No candidate branch with `outcome: FAIL` or `ABANDONED` was merged to a protected branch.
- [ ] `attempts_used` does not exceed `max_attempts`.
- [ ] RER status is `RECOVERED` or, if not, an escalation note names a human owner.
- [ ] Checkpoint records and log bundles are retained for the agreed audit period (default: 30 days).

---

## 8. Configuration reference

| Parameter | Default | Description |
|---|---|---|
| `MAX_REPAIR_ATTEMPTS` | `3` | Maximum repair cycles before the skill halts. |
| `CHECKPOINT_DIR` | `.ai-recovery/checkpoints/` | Where checkpoint records are stored. |
| `LOG_DIR` | `.ai-recovery/logs/` | Where diagnostic log bundles are stored. |
| `PROTECTED_BRANCHES` | `main, master` | Comma-separated list of branches that require a passing RER before merge. |
| `ABANDON_PREFIX` | `abandoned/` | Remote branch prefix for discarded candidates. |
| `LOG_RETENTION_DAYS` | `30` | Days before log bundles may be purged. |

---

## 9. Anti-patterns

| Anti-pattern | Correction |
|---|---|
| Applying an edit without creating a checkpoint first | Phase 1 is mandatory; the skill refuses to proceed without a valid checkpoint |
| Silently retrying after budget exhaustion | Phase 8 is a hard stop; no edit is applied after the budget is exceeded |
| Merging a failed candidate "just to see" | BP-01/02 block the merge unconditionally; require a human override with a written reason |
| Discarding logs from a failed attempt | Phase 6 runs after **every** failure; logs are never optional |
| Trusting a restore without verification | Every restored file is SHA-256 verified (Phase 3 step 2c; Phase 4 step 2) |
| Using branch names instead of commit SHAs in checkpoints | `base_commit` must always be the full 40-character SHA |
| Allowing an `UNRECOVERABLE` RER to remain open indefinitely | The escalation note must name a human owner and a resolution deadline |
