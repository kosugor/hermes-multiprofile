---
name: implement-project-change
description: Implement a scoped repository change and hand off a reproducible revision
  for review.
---

# implement-project-change

## Language

Write internal English in ASD-STE100 style. Use this style for code comments,
reports, and Kanban messages. Write curated wiki prose in Serbian when the task
changes the wiki. Use the operator's language for user-facing replies.

Find the assigned project under `/workspace`. Read its `AGENTS.md` files and
project documentation. Check Git status, relevant code, user edits, and the
acceptance criteria before you edit files.

Use the assigned branch or an authorized isolated project copy. Make the
smallest change that meets the request and follows project conventions. Do not
format unrelated files, upgrade dependencies, or change public APIs. Never use
`reset --hard` or `clean` to remove workspace changes.

Run the smallest relevant checks that the offline environment supports. If a
dependency is missing, name it and run any possible static checks. Do not
change Docker settings. Do not claim a check passed when it did not run. A
network-dependent check can fail because the network is disabled. Do not call
that an application defect.

Inspect the final diff. Remove no user changes. Check for accidental edits and
generated files. Save deliverables under `/workspace`. Hand off the project
path, base revision, new revision or patch, acceptance criteria, commands,
results, and risks. Identify yourself as the implementer. Name the exact
review artifact and its path, commit, revision, or content hash. Attach scratch
outputs when the handoff supports attachments. Ask the Reviewer to review the
same card. Do not merge or publish without authorization.
