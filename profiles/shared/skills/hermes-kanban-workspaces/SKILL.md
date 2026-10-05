---
name: hermes-kanban-workspaces
description: "Use when fixing Kanban Docker workspace blocks."
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, kanban, docker, workspaces, profiles]
---

# Hermes Kanban Workspaces

Diagnose and repair Hermes Kanban tasks blocked by a missing, empty, or wrong Docker workspace without widening access beyond the assigned repository.

## When to Use

- A Kanban worker reports an empty `/workspace`, a missing repository, or `not a git repository`.
- A task prompt confuses a host workspace path with its Docker execution path.
- A profile must be scoped safely to one repository for repeatable Kanban work.

## Procedure

1. **Read current task state before changing configuration.** Discover the board with `hermes kanban boards list`, then use explicit `--board <slug>` for `show`, `runs`, and `log`. A task missing from the default board is not necessarily missing globally. For board-wide advice, inspect `list`, `stats`, and every unfinished task's comments and dependencies. Separate never-dispatched tasks, worker-reported blocks, unsatisfied prerequisites, and actual process failures; refresh these checks on every follow-up rather than reusing an earlier diagnosis. For startup failures, inspect the exact run log before changing workspace settings; `Unknown skill(s)` means resolve the active profile's skill pack, not the Docker mount. For repo-managed deployments, check the active `profiles/<name>/skills/` tree, bootstrap copy behavior, and any explicit expected-skills inventory. A skill in a backup directory is not active; update the source pack and inventory together, then rerun the deployment audit before retrying the task.

2. **Treat paths as two namespaces.** A task workspace such as `dir @ /srv/hermes/wiki` is a host path. With `terminal.docker_mount_cwd_to_workspace: true`, Hermes exposes the configured host CWD inside Docker at `/workspace`. Write task prompts and terminal/file instructions against `/workspace`; retain the host path only in profile configuration and external host-side commands.

3. **Configure a repository-bound profile deliberately.** For a profile dedicated to one repository, set its `terminal.cwd` to that host repository and enable `docker_mount_cwd_to_workspace`. Verify the profile config before unblocking a task. Preserve the intended container isolation; do not enable `container_persistent: true` merely to conceal a lost task mount. Check the task's workspace field separately: `/workspace` is the container execution path, not a host workspace source.

4. **Verify every environment created during the worker run.** Inspect the initial Docker `volume_args`/`run_args` and every later `Creating new docker environment` entry in both assignee logs. Confirm each environment binds the task host path to `/workspace`, then verify `/workspace` is the expected Git worktree. A correct initial mount does not prove later file or terminal tools reused it.

5. **Classify a second empty workspace as a lifecycle bug.** If the initial worker container contains `-v <task-workspace>:/workspace` but a later environment contains `--tmpfs /workspace` without that bind, the dispatcher passed the workspace correctly and the terminal lifecycle lost it. Preserve session isolation: make dispatcher-owned Kanban workers treat their validated `HERMES_KANBAN_WORKSPACE` as a task-scoped mount source for every newly created Docker environment. Add a regression test for the isolated-worker mount and one proving delegated children cannot claim that grant.

6. **Repair the worker's inputs, then requeue.** If the task body names the host path as a container requirement, replace it with `/workspace` and state that it is the mounted execution workspace. Retrieve host-only diagnostics outside the sandbox and put redacted evidence in a worker-readable task comment or attachment; findings in the user's chat are not automatically task context. Confirm the blocker is actually resolved before unblocking, then inspect the next run rather than assuming gateway dispatch occurred. For cron import failures, follow [Worker dependency verification](references/worker-dependencies.md); an import probe is not evidence that the full job completed.

7. **Respect dependency graphs.** If the task was decomposed, let prerequisite children complete and dispatch the consolidation task before expecting the root task to run. Do not force-complete a task with unsatisfied parents.

8. **Close only with evidence.** Verify task status is `done`, inspect its final run/summary, and confirm any requested Git identity, tests, diff, or commit evidence from the actual worker.

## Profile Design

- Keep a profile repository-bound when predictable Docker workspace access matters.
- For multiple unrelated repositories, create repository-specific profiles or use a deliberately generic profile only for tasks that do not require a durable repository mount.
- Do not repeatedly change one shared profile's `terminal.cwd` while Kanban tasks may run concurrently; it is profile-wide state and can route a worker to the wrong repository.

## Pitfalls

- Do not require `/srv/...` to exist inside a Docker worker when it is only the host CWD; Hermes maps that directory to `/workspace` by design.
- Do not add a duplicate bind mount solely to make a host pathname visible in the container; correct the task prompt to use `/workspace` instead, preserving the narrow mount contract.
- Do not interpret empty `HERMES_KANBAN_TASK` or `HERMES_KANBAN_WORKSPACE` as proof that the mounted repository is unavailable; verify `/workspace` and Git directly.
- Do not change `docker_network: false` or `docker_run_as_host_user: false` to fix a workspace mount; neither setting determines the CWD bind mount.
- Do not use `container_persistent: true` as the permanent fix for a session-isolated Kanban workspace loss; it can hide the bug by sharing container state across independent runs instead of preserving the task mount on recreation.
- Do not blame the orchestrator when worker-start logs show the task bind mount. Trace the later environment creation path before changing board, assignee, or profile configuration.
- Do not treat historic blocked-run comments as current state; rerun read-only mount and Git checks after a configuration repair.
- Do not auto-unblock an implementation task whose requested files are untracked and whose acceptance criteria require a commit; first clarify whether adding those files to version control is in scope.

## Safe Recovery and Board Advice

- Distinguish staged changes, tracked modifications, and untracked workflow inputs using `git status --short` and `git diff --cached --name-only`. Apply the actual job contract: expected inbox, checkpoint, report, and backup files do not automatically prohibit a run. Preserve their inventory and fingerprint; never delete or reset user files merely to make Git status clean.
- Separate acceptance criteria by responsibility. Do not interpret a nonempty inbox as a broken semantic index when an index task cannot process clippings. Propose an explicit scope amendment or finish authorized triage first; do not silently waive criteria or force a passing result by deleting inputs.
- Route substantive reviewer findings to an implementation task and independent review. Check the supported review lifecycle before requesting changes: a separately created reviewer card claimed from ready/running may not support the same transition as a task in review.
- Recommend recovery in dependency order, not bulk unblocking. For orchestrator handoffs, provide one copyable, ordered message with identifiers preserved, evidence-transfer steps, safety gates, and required verification. Clearly distinguish recommended actions from changes already executed.
- Require explicit authorization for a production rerun. Snapshot initial inputs, check staged changes and active maintenance workers, run at most once when authorized, inspect the execution ID and ownership acknowledgement, and preserve a paused schedule unless resuming it is separately requested.

## Verification Checklist

- [ ] Task body uses `/workspace` for in-container operations.
- [ ] Dedicated profile CWD points to the intended host repository.
- [ ] Docker worker sees `/workspace` as the expected Git worktree.
- [ ] Task was unblocked and dispatched after the repair.
- [ ] The new run completed or produced a current, exact blocker.
- [ ] Dependency and final task statuses are consistent.
