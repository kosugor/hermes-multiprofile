---
name: docsite-clipper
description: "Crawl docs sites by clipping each page with Clipper."
version: 0.2.0
author: Goran Kosutic, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [documentation, crawling, clipping, markdown, obsidian]
    related_skills: [clipper, obsidian, source-access-triage]
---

# Docsite Clipper Skill

Discover every reachable in-scope documentation page from a supplied root URL, then process **each English page individually through the `clipper` skill**. When a site exposes multiple languages, English is the default and non-English pages are excluded. The discovery helper only produces a manifest; it must not create page notes or replace Clipper's browser-based extraction, cleanup, template handling, or duplicate policy.

## When to Use

- Use when the user asks to clip or archive a bounded documentation site into Obsidian.
- Use when every discovered documentation page must follow the same Clipper capture contract.
- Don't use for a single page; use `clipper` directly.
- Don't use for blocked-source recovery or final wiki synthesis.

## Prerequisites

- A root documentation URL, such as `https://example.org/docs/`.
- A resolved Obsidian vault/wiki root containing the requested destination.
- `browser_exec` access to load each page.
- The `clipper` skill loaded and followed separately for every English page.
- No credentials are accepted. If a page requires login, stop at that page and report the boundary.
- A headless Chromium with remote debugging (CDP) available. If `browser_exec` cannot auto-launch Chrome or the installed `browser-use` CLI has no `browser_helpers` module, start Playwright Chromium in the background yourself (`~/.cache/ms-playwright/chromium-*/chrome-linux-arm64/chrome --headless=new --no-sandbox --remote-debugging-port=9224 …`) and use `clipper/scripts/cdp_capture.py` for per-page capture.

## How to Run

First discover URLs and write the manifest:

```text
terminal(command="python ~/.hermes/skills/note-taking/docsite-clipper/scripts/discover_docsite.py --root 'https://example.org/docs/' --wiki-root '/path/to/wiki'", timeout=600)
```

Optional flags:

```text
--delay 0.2                 pause between discovery requests
--max-pages 10000           safety ceiling
--timeout 30                per-request timeout
--user-agent '...'          override the request user agent
--exclude-prefix URL       skip a canonical URL prefix; may be repeated
```

The manifest is written to `<wiki-root>/raw/site/<host>/_crawl-report.json`. It lists discovered pages under `pages[]`, including the deterministic target filename in `pages[].file`.

## Quick Reference

- Discovery helper: `scripts/discover_docsite.py`.
- Manifest: `<wiki-root>/raw/site/<host>/_crawl-report.json`.
- Page list and mapping: `pages[].url` → `pages[].file`.
- Per-page capture: load `clipper`, then use its browser capture procedure.
- Final note verification: use Clipper's `read_file` verification for each destination.

## Procedure

1. **Set the boundary.** Confirm the root URL, wiki root, destination folder/template, and duplicate policy. The normalized root is an exhaustive scope boundary: same scheme and authority, with paths under the root path.
   - Completion criterion: scope and output policy are explicit.

2. **Discover the site.** Run `scripts/discover_docsite.py` with an explicit root and wiki root. It follows reachable in-scope HTML links, skips non-HTML assets and pages identified as non-English from their `<html lang>` or obvious locale path segment, records redirects and errors, and writes the manifest.
   - Completion criterion: the command exits successfully, the manifest exists, and its `pages` list is available.

3. **Check discovery limits.** Read `_crawl-report.json` and inspect `visited`, `discovered`, `skipped`, `errors`, and `max_pages_reached`. Treat `errors`, login walls, rate limits, robots restrictions, and out-of-scope redirects as evidence boundaries. Do not claim complete coverage when any material boundary remains.
   - Completion criterion: the exact page set to process and any excluded/unavailable URLs are recorded.

4. **Clip pages one at a time.** For every English entry in `pages[]`, load the `clipper` skill and execute its complete page-capture procedure: inspect the live browser page, extract readable content, convert it to Markdown, resolve the destination, handle duplicates safely, write the note, and read it back. If the live page proves non-English, skip it and record the reason. Do not use the discovery helper's HTML text as the note body. Do not batch-write pages or bypass Clipper.
   - Completion criterion: each listed URL has either a verified Clipper note or a recorded per-page failure/boundary/locale exclusion.

5. **Rewrite internal relative links.** While converting each page through `clipper`, resolve every relative HTML link against that page's URL. If its canonical target is present in the manifest, replace the link target with the target's `pages[].file` filename and retain any fragment. For example, `/docs/user-guide/profiles` becomes `docs-user-guide--profiles.md`. Keep external, asset, and unresolved links unchanged.
   - Completion criterion: every resolved in-scope page-to-page link points to the manifest filename, never back to the original HTML URL.

6. **Preserve provenance.** Keep each clipped note's source URL and the discovery manifest. If the canonical URL differs from the captured URL, preserve both according to Clipper's rules. Do not summarize, rename, or delete clipped notes unless separately requested.
   - Completion criterion: every successful note remains traceable to its exact source URL.

7. **Reconcile counts.** Compare the manifest page count with the per-page results programmatically or from a durable results file. Re-fetch or investigate if the counts disagree; never report a partial set as complete.
   - Completion criterion: `listed = successful + failed`, with every URL accounted for exactly once.

## Per-Page Clipper Contract

For each discovered URL, Clipper must:

- use a real browser page as the primary source;
- preserve observed title and canonical/source URL;
- remove obvious navigation and other page chrome while retaining notices, headings, lists, links, tables, quotes, and code;
- apply the requested template, folder, tags, and metadata, or Clipper's documented default when none is supplied;
- check for duplicates before writing and never overwrite silently;
- verify the exact written note with `read_file`;
- record a partial/blocked extraction instead of inventing missing content.

## Pitfalls

- The discovery helper is not a Markdown capture pipeline. Its `pages[].title` is discovery metadata only; never copy its flattened HTML text into notes.
- English-only is detected conservatively from `<html lang>` and obvious locale path segments; if a page's language is ambiguous, inspect it in the browser before clipping and exclude it only when non-English is confirmed.
- A non-English page must never be imported merely because it appears in navigation or as an alternate-language link. Keep the exclusion reason in the manifest/results.
- Use the manifest's `pages[].file` mapping rather than regenerating filenames during clipping; collision suffixes must be preserved exactly.
- Relative links that do not resolve to a discovered page remain unchanged; never invent a local filename.
- JavaScript-rendered pages may be discoverable but require browser rendering during Clipper capture.
- A root ending in `/docs/` excludes sibling paths such as `/blog/` and `/`.
- Sitemap discovery is not used; only links reachable from fetched in-scope pages are discovered.
- A site can change during a long run. If the manifest is stale or a page redirects, use the live-page result and record the discrepancy.
- Do not infer page content from titles, snippets, or failed fetches.
- Do not claim full ingestion when the helper hit `--max-pages`, or when any listed page lacks a verified Clipper result.
- `browser_exec` and the `browser-use` CLI (≥0.1.x) cannot always launch a Chromium (no `browser_helpers` module). For batch docsite capture, start Playwright Chromium in the background and loop `clipper/scripts/cdp_capture.py:capture_url(port, url)` — it returns a clean dict with title, canonical, headings, tables, and body without cookie-consent noise. Close each tab after capture to keep memory flat.
- `scripts/discover_docsite.py` has a host-only-root bug: when the supplied root has an empty path (e.g. `https://api-docs.deepseek.com/` after `rstrip('/')`), the `in_scope` check matches the literal `'/'` and rejects every other in-scope path. Detect this by reading `_crawl-report.json` after discovery — if `pages` is empty but the root URL is reachable and has discoverable links, write a small custom manifest generator that manually enumerates the URLs (root + guides + quick_start + updates, etc.) and emits the same `<host>/_crawl-report.json` shape with the same `pages[].file` naming, then run the per-page clipper on it. Do not patch `discover_docsite.py` mid-run.
- After every capture run, the file `cdp_capture.py` writes is sensitive to a single extra cookie-banner button; the SHA-256 is therefore a poor "did the content change?" signal across runs. Use byte size + a structural spot-check (first heading, table row count) as the change test, and reserve the SHA for file-identity within a single run.

## Verification

A docsite clip run is complete only when:

- the manifest exists and has no unreported discovery error or page-limit boundary;
- every URL in `pages[].url` has exactly one result, including a recorded non-English exclusion where applicable;
- every successful result was produced by the `clipper` skill, not the discovery helper;
- each successful note is inside the resolved vault, contains the source URL, and passes Clipper's read-back verification;
- failed or blocked pages are explicitly listed with their reason;
- the final successful/failed totals reconcile exactly with the manifest page count.
