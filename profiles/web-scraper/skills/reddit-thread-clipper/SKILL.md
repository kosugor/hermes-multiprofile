---
name: reddit-thread-clipper
description: Clip Reddit threads with comments and source metadata.
version: 0.1.0
author: Goran Kosutic, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [reddit, clipping, obsidian, comments, provenance]
    related_skills: [web-clipper]
    requires_toolsets: [web, browser, file]
---

# Reddit Thread Clipper

Capture a supplied Reddit post and its visible discussion as a faithful Markdown
source. Preserve post and comment structure, provenance, and capture limits. Do
not summarize the thread or treat comments as verified facts.

## When to Use

- The user or Orchestrator supplies a Reddit post or comment URL to clip.
- A wiki task explicitly asks to preserve a Reddit discussion as source material.

Do not use this skill to search Reddit for new threads, write or vote on Reddit,
or infer missing posts or comments.

## Prerequisites

- Use only the supplied URL unless the task explicitly requests discovery.
- Use `web_extract` first. Use the built-in browser tools only to inspect the
  same public URL when extraction is incomplete and browser access is permitted.
- Do not sign in, bypass access controls, solve CAPTCHAs, or use undocumented
  endpoints to evade restrictions. If Reddit requires authentication or blocks
  access, mark the capture partial or failed and report the limitation.
- For a Kanban `dir` workspace, verify `/workspace` is the mounted wiki by
  checking `git -C /workspace rev-parse --show-toplevel` returns `/workspace`.
  Do not use a host path inside the container.
- Before reading, searching, or writing a wiki file, acquire the shared lock:
  `python3 /workspace/.hermes-maintenance/wiki-writer-lock.py acquire --owner kanban:<task-id>:web-scraper`.
  Keep the token through validation. Release it with
  `python3 /workspace/.hermes-maintenance/wiki-writer-lock.py release --token <token>`.
  If the lock is busy, stop and report the wait; never bypass or remove it.

## Procedure

1. Keep the supplied URL and canonical post URL separate. Remove tracking
   parameters only when safe. Do not replace a comment permalink with the post
   URL without recording both.
2. Retrieve the supplied URL with `web_extract`. Inspect the title, post body,
   author, subreddit, posted time, and visible comments. If the result is an
   error page, login wall, empty shell, or lacks the requested discussion, do
   not label it complete. If permitted, inspect the same URL with browser tools.
3. Preserve the post title and body verbatim, including language, links, code,
   and quoted text. Do not correct grammar, translate, or summarize.
4. Preserve visible comments as a tree in source order. For each captured
   comment, retain its visible author, text, timestamp when shown, score when
   shown, and permalink when available. Keep replies nested under their parent.
   Do not invent fields or reorder by score. Mark deleted/removed text as such;
   do not reconstruct it. A comment's score and visibility are a snapshot, not
   stable facts.
5. State the capture boundary: whether comments are top-level only, include
   visible replies, are truncated, or omit collapsed/unavailable branches.
   Never imply the complete Reddit thread was captured unless the source
   explicitly exposed all of it and you verified that coverage.
6. Save a Markdown clipping with exactly one H1. Use the post permalink as
   `canonical_url`; keep the supplied URL in `supplied_url`. Use the existing
   `web-clipper` metadata fields and add:
   `platform: reddit`, `subreddit`, `post_author`, `post_score_at_capture`,
   `comments_captured`, and `thread_coverage`. Use `unknown` when the source
   does not expose a value. Set `capture_limitations` to a concise list or
   `none`. Set `capture_status` accurately to `complete`, `partial`, `shell`,
   or `failed`.
7. Save under `/workspace/Inbox/Clippings/` unless the task gives another
   workspace-relative path. Use a unique timestamped filename; never overwrite
   an earlier capture. Follow the filename pattern in `web-clipper`.
8. Calculate `content_sha256` over the exact saved Markdown body bytes after
   frontmatter. Run the existing `web-clipper/scripts/validate-capture.py` on
   the saved file. Read it again and verify links, metadata, comment nesting,
   capture boundary, hash, and status. Repeat the Git-root check before
   finishing. Release the writer lock after validation.
9. Report the workspace-relative path, canonical permalink, status, and any
   missing or truncated content. Do not claim a host-side file was written
   unless the workspace check proves it.

## Pitfalls

- Reddit pages can expose only a subset of a thread. A successful page load does
  not prove comment completeness.
- Scores, sorting, deleted comments, collapsed replies, and edited labels can
  change or be unavailable. Record only what was visible at capture time.
- A post author's claim is a source statement, not independent confirmation.
- A browser login wall or challenge page is not source content. Do not mark it
  complete or clip the boilerplate as if it were the thread.
- The generic capture validator checks frontmatter, body hash, and disposition;
  it does not validate that the comment tree is complete.

## Verification

- `web-clipper/scripts/validate-capture.py` reports success.
- The saved body has one H1 and the captured comment hierarchy is readable.
- Each captured post/comment link points to the corresponding Reddit item when
  the source exposed a permalink.
- `thread_coverage`, `comments_captured`, and `capture_limitations` agree with
  what the source actually displayed.
- The body hash matches the exact saved body bytes, and the wiki lock is released.
