---
name: web-clipper
description: Save a supplied URL as Obsidian Markdown. Use Firecrawl first.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [obsidian, clipping, markdown, firecrawl, browser]
    category: note-taking
    requires_toolsets: [web, browser, file]
---

# Web Clipper

## Language

Follow ASD-STE100 Issue 9 for internal English. Use short sentences, active
verbs, and one term for one meaning in Kanban messages and reports.
Preserve captured text in its original language. Do not translate raw captures.
Use the operator's language for user-facing replies.

## Input

Use a URL that the user or Orchestrator supplies. The Telegram command is
`clip <absolute HTTP(S) URL>`. Do not treat another URL as a clipping request.

## Procedure

For a Kanban `dir` workspace, `workspace_path` is the host mount path. It does
not need to exist inside Docker. Hermes mounts it at `/workspace`. Check that
`/workspace` exists and is writable. For wiki clipping, check that
`/workspace/.git` exists. Run `git -C /workspace rev-parse --show-toplevel`.
It must return `/workspace`. This check proves that `/workspace` is the wiki.
Do not accept an empty container folder. Do not check for `/srv/hermes/wiki` in
Docker or block because it is absent.

Before you read, search, or write a wiki file, run
`python3 /workspace/.hermes-maintenance/wiki-writer-lock.py acquire --owner
kanban:<task-id>:web-scraper`. Keep the token through validation. Then run
`python3 /workspace/.hermes-maintenance/wiki-writer-lock.py release --token
<token>` with that token. Wiki Maintainer, Kanban, and cron use the same lock.
If you cannot acquire it, stop. Bootstrap and `install-wiki-triage.sh` install
the helper.

1. Normalize the URL. Remove clear tracking parameters when safe.
2. Call `web_extract` with Firecrawl. Keep the supplied URL and canonical URL
   as separate values. Record a publication or update date only when the page
   states one. Otherwise, use `unknown`.
3. Check extraction quality:
   - title present;
   - main body present;
   - headings/links/code preserved reasonably;
   - no dominant navigation or boilerplate.
4. If extraction is incomplete, blocked, needs JavaScript, or needs interaction,
   use the local browser tools and managed Chromium. `browser.backend: "off"`
   turns off Browser Use CLI. It does not turn off these built-in tools. If
   neither tool gets the source body, keep the evidence. Set status to `shell`
   or `failed`.
5. Write clean Markdown:
   - Use one H1 title.
   - Keep the source's heading order.
   - Keep code blocks, tables, lists, quotes, and useful links.
   - Remove menus, related posts, ads, cookie notices, and repeated footers.
   - Keep the author's words. Change formatting only. Do not write an AI summary.
6. Add source details to the frontmatter. Quote values when YAML needs quotes:

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

7. Use this filename form:
   `<UTC timestamp with microseconds>-<title-slug>-<first-8-hash-chars>.md`.
   Example: `20260921T033000123456Z-title-a1b2c3d4.md`. If the name exists, add
   a number. Do not overwrite a file. Keep each dated capture of a URL.
8. Save the file to `/workspace/Inbox/Clippings/<filename>.md`, unless the task
   gives another workspace-relative path. Create the target folder if needed.
   The host path `/srv/hermes/wiki/Inbox/Clippings` maps to this container path.
   It does not change the `/workspace` mount.
9. Run `scripts/validate-capture.py` on the saved file. Return its path and a
   short description. Before you finish, repeat the Git-root check. Confirm
   that the file is readable under `/workspace`. If the check fails, block the
   task. State that Docker used an ephemeral workspace. Do not claim that the
   file exists on the host.

## Search Rule

Do not use `web_search` just because it is available. The supplied URL is the
source of truth. Search only when the task asks for related sources or you
cannot resolve the canonical URL.

## Fidelity Rule

Do not summarize a clipping. Keep the source content. Condense it only when the
user asks for a summary.

## Verification

Read the saved Markdown again. Confirm that:
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
