---
name: wiki-task-coordination
description: Coordinate wiki Kanban tasks without writer-lock conflicts.
version: 0.1.0
author: Goran Kosutic, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [wiki, kanban, coordination, writer-lock, scheduling]
    related_skills: [hermes-kanban-workspaces]
---

# Wiki Task Coordination

Coordinate Kanban tasks that read or write the shared wiki vault. Keep writer
operations serial. Treat a held writer lock as a temporary dependency, not as
permission to bypass the lock or as proof that a task is permanently blocked.
This skill manages task order. It does not inspect or edit wiki files.

## When to Use

Use this skill when:

- Web Scraper and Wiki Maintainer tasks target the same wiki;
- a worker reports that it cannot acquire the shared wiki writer lock;
- several wiki tasks are ready or running at the same time;
- a wiki task is blocked after lock contention or a worker startup failure;
- a task needs a safe recovery order after a lock holder finishes.

Do not use it to diagnose a code change in the Kanban dispatcher. Report
repeated dispatcher or worker crashes as runtime failures and preserve their
run evidence.

## Tools and Board Scope

Use native Kanban tools. Read the board and task state before any transition.
Use the explicit `wiki` board for the wiki vault. Do not assume that the current
board is `wiki`. Confirm the task's board context before any state-changing
action. If the tools do not expose the board scope, stop and request an operator
check rather than changing another board.

Use `kanban_list`, `kanban_show`, `kanban_comment`, `kanban_link`, and
`kanban_unblock` only when their action is needed and supported by the current
task state. Preserve task identifiers exactly. Do not create duplicate tasks to
replace a blocked task.

## Coordination Procedure

1. Read the current board state. Inspect the target task, its dependencies,
   comments, latest runs, and any active lock owner reported by a worker.
   Completion means the task's present status and latest failure are known.
2. Classify the condition:
   - **Lock busy:** another identified task owns the wiki writer lock.
   - **Workspace failure:** `/workspace` is empty, is not the expected Git root,
     or does not contain the assigned repository.
   - **Startup/runtime failure:** the worker exits before doing task work, such
     as `Unknown skill(s)`, a process crash, or tool initialization failure.
   - **Task dependency:** a required parent or prerequisite is still open.
   Do not label one class as another.
3. Serialize wiki writers. Allow no more than one task that may write the shared
   vault to run at a time. This includes Web Scraper clipping writes and Wiki
   Maintainer triage or edits. Let read-only review run only when it does not
   acquire or change the shared vault state.
4. If the lock is busy, do not dispatch another writer. Keep the waiting task
   pending in `todo` when possible. If the task is already `blocked`, record a
   concise comment with the lock owner and the task that must finish. Do not
   repeatedly unblock or dispatch it while the same owner holds the lock.
5. If a second writer has not started and the dispatcher could start it before
   the current writer releases the lock, link the active writer task as a parent
   of the waiting task with `kanban_link`, if the task state and graph allow it.
   Comment that this edge serializes access to the shared writer lock. Check for
   cycles first. Do not use a dependency edge when the active task is already
   complete or when the link would misrepresent an unrelated content dependency.
6. Never remove, replace, or ignore a lock because it appears old. The lock
   owner or an authorized operator must confirm release. A worker report of
   `locked=false` is evidence; elapsed time alone is not.
7. After the owner finishes, verify the latest task state and lock-release
   evidence. If the waiting task remains blocked only because of this resolved
   contention, add a short comment that records the resolution, then use the
   supported unblock action once. Confirm that it returns to the correct state
   and dispatch it once.
8. For a workspace failure, use `hermes-kanban-workspaces`. Require task
   instructions to use `/workspace` inside Docker and require the configured
   host workspace to be the correct repository. Do not add duplicate mounts or
   weaken container isolation.
9. For a startup/runtime failure, inspect the exact run error before retrying.
   An `Unknown skill(s)` error requires the missing skill in the active profile's
   managed skill pack and inventory. A process crash requires runtime
   investigation. Do not retry repeatedly or change the workspace mount without
   evidence.
10. Respect parent-child task order. Do not unblock a consolidation task while
    its required children remain open. Do not force-complete a task to clear a
    queue.
11. Verify the outcome from the board. Confirm the waiting task has one new
    attempt after the dependency clears, and that it completes or reports a
    current, specific blocker. Do not infer dispatch from a successful unblock.

## Safety Rules

- The shared writer lock is the authority for wiki write access. This skill
  cannot grant or transfer lock ownership.
- Never ask a worker to bypass lock acquisition or write without the lock.
- Never tell a worker to release another task's lock.
- Never bulk-unblock wiki tasks.
- Never treat an old blocked comment as current state. Re-read the task, runs,
  and lock evidence before recovery.
- Keep one writer active even when the Kanban dispatcher can start more workers.
- Do not expose lock tokens, credentials, or private source content in task
  comments.

## Report Format

For a coordination decision, report:

```text
Board: wiki
Task: <task-id>
Condition: lock-busy | workspace-failure | startup/runtime-failure | dependency
Evidence: <current run, comment, owner, or dependency>
Action: <queued | linked | unblocked once | escalated>
Next gate: <specific event or verification needed>
```

Separate the recommended action from any action already completed. If the
current board or lock state cannot be read, say so and do not change task state.

## Verification

Coordination is complete only when:

- the explicit `wiki` board and current task state were checked;
- lock contention, workspace failure, runtime failure, and task dependency were
  distinguished using current evidence;
- no two wiki writers were dispatched concurrently;
- no lock was bypassed or removed;
- any unblock was followed by a verified new run or a current blocker;
- parent-child dependencies remain satisfied;
- the report identifies evidence and the next gate.
