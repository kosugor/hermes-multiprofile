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

A URL supplied by the user or orchestrator.

## Procedure

1. Normalize the URL and remove obvious tracking parameters when safe.
2. Call `web_extract` using Firecrawl.
3. Evaluate extraction quality:
   - title present;
   - main body present;
   - headings/links/code preserved reasonably;
   - no dominant navigation or boilerplate.
4. If extraction is incomplete, JavaScript-dependent, blocked, or requires
   interaction, use the enabled browser to reach the content and capture the
   useful body.
5. Produce clean Markdown:
   - one H1 title;
   - preserve meaningful heading hierarchy;
   - preserve code blocks, tables, lists, quotations, and useful links;
   - remove menus, related-post grids, ads, cookie notices, repetitive footers;
   - avoid rewriting the author's wording except for formatting cleanup.
6. Add provenance frontmatter:

   ---
   title: "<page title>"
   source: "<canonical URL>"
   clipped: "<YYYY-MM-DD>"
   ---

7. Choose a filesystem-safe filename based on the title.
8. Save to `/workspace/Inbox/Web Clips/<filename>.md` unless the task specifies
   a different workspace-relative destination.
9. Run `scripts/validate-capture.py` on the saved Markdown and return the
   created file path plus a one-sentence description.

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
- source URL is present;
- no obvious site chrome remains;
- no section was accidentally duplicated;
- code fences and Markdown structure are balanced;
- `scripts/validate-capture.py` reports success.
