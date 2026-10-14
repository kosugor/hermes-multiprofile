---
name: medium-article-ingestion
description: Use when ingesting Medium articles. Recover body and URL.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [medium, article, ingestion, web, provenance, wiki]
    category: note-taking
    related_skills: [obsidian-wiki-ingestion, consent-walled-web-ingestion, source-access-triage, ai-wiki-ingestion]
---

# Medium Article Ingestion

Use this skill when the source is a Medium article or publication page and the goal is to ingest it into an Obsidian-backed wiki.

## When to use
- User provides a `medium.com` URL
- Medium returns a member wall, preview shell, or Cloudflare block
- You need a durable raw article capture with provenance
- The article is substantial enough to justify a focused concept/summary page

## Workflow

1. **Orient on the destination wiki first.**
   - Read `SCHEMA.md`, `index.md`, and recent `log.md`.
   - Search for the article topic before creating new pages.
   - Resolve the real vault path if the user names a wiki loosely.

2. **Recover the article body.**
   - Prefer the free/share Medium link (`?sk=...`) when one exists; use it as the main readable source for ingestion.
   - If there is no free/share link, or it still does not expose the body, try the canonical Medium URL.
   - If normal extraction fails, try one of these fallbacks in order:
     - `r.jina.ai/http://...` or `https://r.jina.ai/http://...`
     - direct HTTP fetch with a browser-like User-Agent
     - page metadata / JSON-LD / embedded article text
   - Treat Medium paywalls or member gates as access problems, not proof the body is unavailable.

3. **Preserve both canonical and recoverable URLs.**
   - Keep the user-provided Medium URL in `source_url` when possible.
   - If the readable body comes from a free/share URL (`?sk=...`) or mirror, keep that path in a separate provenance field or note line.
   - Record the exact recovery path in the raw note body.

4. **Write the raw capture.**
   - Save the article under `raw/articles/`.
   - Include frontmatter with at least:
     - `source_url`
     - `ingested`
     - `sha256`
   - Also capture, when available:
     - title
     - author
     - published date
     - canonical/share URL distinctions
     - access notes (`r.jina.ai`, direct HTML, member wall, etc.)
   - Hash only the final body below frontmatter after the last edit.

5. **Create or update a focused wiki page when the article matters.**
   - If the Medium piece is central to a durable topic, create a small concept page that captures the claim, takeaway, and evidence boundary.
   - Do not force every article into a new page; if it is just a source in a broader cluster, a raw note may be enough.
   - Keep uncertainty explicit when the article is opinionated, predictive, or based on secondary citations.

6. **Update navigation and provenance.**
   - Add any new wiki page to `index.md`.
   - Append a `log.md` entry listing the source URL, raw file, and any created/updated pages.
   - Verify the raw file exists and the stored hash matches the final body.

## Medium-specific cues
- Many Medium articles expose a free/share URL separate from the canonical article URL.
- `r.jina.ai` often recovers readable markdown even when the live site blocks direct fetch.
- Publication pages can redirect to a member wall; keep the provenance of the readable body explicit.
- A Medium article can be republished or mirrored elsewhere; do not silently collapse those sources unless the canonical relation is clear.

## Pitfalls
- Do not stop at the first 403 or member wall.
- Do not invent body details from the slug, title, or image captions alone.
- Do not discard the share URL if that is the only readable path.
- Do not create a large topic page when a single raw capture is all the article justifies.
- Do not forget to rehash the raw body after every final edit.

## Verification checklist
- [ ] Canonical Medium URL tested
- [ ] At least one readable path recovered or a clear access ceiling recorded
- [ ] Raw note saved under `raw/articles/`
- [ ] `sha256` matches the exact written body
- [ ] New wiki page created only if the article is durable enough to justify it
- [ ] `index.md` and `log.md` updated when pages were added or changed
