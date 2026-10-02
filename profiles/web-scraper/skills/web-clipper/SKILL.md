---
name: web-clipper
description: Convert a supplied URL into clean Obsidian Markdown using Firecrawl first and the enabled browser only when extraction needs a real browser.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [obsidian, clipping, markdown, firecrawl, browser]
    category: note-taking
    requires_toolsets: [web, browser, file]
---

# Web Clipper

## Input

A URL supplied by the user or orchestrator. The Telegram-facing command is
`clip <absolute HTTP(S) URL>`; do not treat an ordinary URL in an unrelated
message as a clipping request.

## Procedure

For a Kanban `dir` workspace, treat the task's absolute `workspace_path` as the
host-side bind-mount source, not as a path that should exist inside Docker.
Hermes exposes it to terminal and file operations at `/workspace`. At startup,
verify `/workspace` exists and is writable. For the configured wiki clipping
workflow, also require `/workspace/.git` to exist and require
`git -C /workspace rev-parse --show-toplevel` to resolve to `/workspace`. This is
the mount canary: an empty, container-local `/workspace` is not the wiki and
must never be accepted. Do not inspect `/srv/hermes/wiki` or block merely
because that host path is absent inside the sandbox.

Before reading/searching or writing any wiki file, run
`python3 /workspace/.hermes-maintenance/wiki-writer-lock.py acquire --owner
kanban:<task-id>:web-scraper`. Retain the returned token through artifact
read-back and capture validation, then run
`python3 /workspace/.hermes-maintenance/wiki-writer-lock.py release --token
<token>` with that exact token. This same lock protects Wiki Maintainer Kanban
and cron edits. If acquisition fails, block without wiki work. The helper is
installed by bootstrap and `install-wiki-triage.sh`.

1. Normalize the URL and remove obvious tracking parameters when safe.
2. Call `web_extract` using Firecrawl. Preserve the supplied URL separately
   from any canonical URL returned by the page. Record publication/update date
   only when the page states one; otherwise use `unknown`.
3. Evaluate extraction quality:
   - title present;
   - main body present;
   - headings/links/code preserved reasonably;
   - no dominant navigation or boilerplate.
4. If extraction is incomplete, JavaScript-dependent, blocked, or requires
   interaction, use the built-in local browser tools and managed Chromium.
   `browser.backend: "off"` opts out of Browser Use CLI and does not disable
   these built-in tools. If neither path captures the substantive body, retain
   the observed evidence and classify it as `shell` or `failed`.
5. Produce clean Markdown:
   - one H1 title;
   - preserve meaningful heading hierarchy;
   - preserve code blocks, tables, lists, quotations, and useful links;
   - remove menus, related-post grids, ads, cookie notices, repetitive footers;
   - avoid rewriting the author's wording except for formatting cleanup. Do not
     replace the clipping with an AI-generated summary.
6. Add provenance frontmatter. Quote values when needed so the frontmatter
   remains valid YAML:

   ---
   title: "<page title>"
   supplied_url: "<URL supplied in the task>"
   canonical_url: "<canonical URL, or supplied URL if unchanged>"
   source: "<same canonical URL; kept for legacy triage compatibility>"
   published_at: "<date or unknown>"
   clipped: "<YYYY-MM-DD>"
   retrieved_at: "<UTC ISO-8601 timestamp ending in Z>"
   capture_status: "complete|partial|shell|failed"
   capture_method: "firecrawl|browser|firecrawl+browser"
   capture_limitations: "<none, or concise list of omissions/restrictions>"
   provider: "<provider used for this run>"
   model: "<model used for this run>"
   content_sha256: "<SHA-256 of the exact saved body bytes after frontmatter>"
   ---

7. Choose a filesystem-safe filename in the form
   `<UTC timestamp with microseconds>-<title-slug>-<first-8-hash-chars>.md`
   (for example, `20260921T033000123456Z-title-a1b2c3d4.md`). If a collision
   still occurs, append a numeric suffix rather than overwriting. This
   preserves a dated snapshot when the same URL is clipped more than once.
8. Save to `/workspace/Inbox/Clippings/<filename>.md` unless the task
   specifies a different workspace-relative destination. Create the directory
   if it does not exist. A task referring to the host destination
   `/srv/hermes/wiki/Inbox/Clippings` maps to this same container path; it does
   not override the `/workspace` mount point.
9. Run `scripts/validate-capture.py` on the saved Markdown and return the
   created file path plus a one-sentence description. Before completing the
   task, re-run the Git-root canary and confirm the new file is readable from
   that same `/workspace`. If the canary fails, block the task and explicitly
   state that the Docker workspace was ephemeral; never claim a host-equivalent
   path.

## Search Rule

Do not use `web_search` merely because it is available in the `web` toolset.
The supplied URL is the source of truth. Search only if the task explicitly
asks for related material or the canonical source cannot be resolved.

## Fidelity Rule

Clipping is not summarization. Preserve the meaningful article/page content.
Only condense if the user explicitly asks for a summary.

## Verification

Re-read the saved Markdown and confirm:
- frontmatter is valid;
- supplied and canonical URLs are present;
- retrieval timestamp, capture metadata, provider/model, and body hash are
  present and the body hash matches;
- status is accurate: `complete`, `partial`, `shell`, or `failed`; shell and
  failed captures are never presented as complete sources;
- no obvious site chrome remains;
- no section was accidentally duplicated;
- code fences and Markdown structure are balanced;
- `scripts/validate-capture.py` reports success.
