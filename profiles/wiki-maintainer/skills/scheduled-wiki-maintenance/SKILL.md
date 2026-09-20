---
name: scheduled-wiki-maintenance
description: Run bounded recurring Obsidian maintenance with persistent checkpoints and a concise report.
---

# Scheduled wiki maintenance

Read the cron prompt as the scope of this run. Load maintain-obsidian-wiki and audit-vault-links. Use the assigned /workspace through the Docker tools. Keep LCM, offline execution and current mounts unchanged.

Use /workspace/.hermes-maintenance/ for a checkpoint and run reports. Exclude this directory and .hermes-backups from content/link indexing. At the start, read the prior checkpoint if present. For the first run, inventory relevant Markdown notes and follow the prompt's scope; do not infer that a whole-vault rewrite is authorized.

For routine maintenance, inspect notes added or changed since the last successful pass and their link targets/backlinks. Account for timestamp ties or backdated sync using stored path/content hashes when practical. Process at most 20 changed notes per run; record remaining paths so later runs resume instead of restarting the entire vault.

Apply only unambiguous in-scope link repairs and updates to already-existing indexes where the intended convention is evident. Preserve prose and metadata. Report ambiguous targets, duplicate topics, missing source evidence and possible merges. Do not rename/delete notes, change the taxonomy or rewrite article content under a generic recurring-maintenance instruction. Explicitly authorized jobs may define a broader scope.

Before editing, retain affected originals using maintain-obsidian-wiki. Compare the current file with the version read before replacing it; if another writer changed it, skip and report the conflict. Cron concurrency limits do not serialize Kanban jobs, Obsidian Sync or human edits. Do not start a second maintenance pass while another known vault maintenance task is active; report a skipped run instead. This coordination is behavioral, not a filesystem lock.

Write a dated report under /workspace/.hermes-maintenance/reports/ with examined and changed paths, validation, unresolved issues and remaining work. Save checkpoint updates atomically only for successfully processed files. On partial failure retain the previous checkpoint for unfinished items. Return a concise report with workspace paths and any needed follow-up; do not use Kanban completion tools without a real assigned task.

Never reschedule yourself. QMD refresh remains with the owner's existing host indexing workflow. Report changed paths for that refresh; do not add QMD or web tools here.
