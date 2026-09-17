---
name: implement-project-change
description: Implement a scoped repository change and hand off a reproducible revision
  for review.
---

# implement-project-change

Locate the assigned project under `/workspace`. Read applicable AGENTS.md and project documentation. Inspect git status and the relevant code before changing files; identify user edits and the requested acceptance behavior.

Use an assigned branch or authorized isolated project copy. Make the smallest coherent implementation consistent with the project's conventions. Avoid unrelated formatting, dependency upgrades and public API changes. Never use reset --hard or clean to discard a dirty workspace.

Run the narrow relevant checks supported by the prebuilt offline environment. If dependencies are missing, provide the exact missing prerequisite and any static checks possible; do not change Docker settings or pretend a test passed. Existing network-dependent checks may fail because networking is disabled: distinguish that from an application defect.

Inspect the final diff for accidental edits and generated junk. Persist deliverables under `/workspace`. Hand off project path, base revision, changed revision or explicit patch, acceptance criteria, commands and results, and remaining risks. Ask for review via the task's supported review workflow and name reviewer. Do not merge or publish without authorization.
