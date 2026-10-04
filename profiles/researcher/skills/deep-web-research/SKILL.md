---
name: deep-web-research
description: Research web questions with SearXNG, Firecrawl, and the built-in browser.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [research, web, searxng, firecrawl, camofox, citations]
    category: research
    requires_toolsets: [web]
---

# Deep Web Research

## Language

Write internal English in ASD-STE100 style. Use this style for research reports,
claim ledgers, and Kanban messages. Keep source quotations in their original
language. Use the operator's language for user-facing replies.

## When to Use

Use this workflow for broad web research, current technical questions, product
comparisons, documentation checks, and tasks that need source comparisons.

## Procedure

1. Restate the research question internally as concrete subquestions.
2. Search SearXNG with several focused queries.
3. Prefer primary sources:
   - official documentation and repositories;
   - standards bodies and specifications;
   - vendor release notes;
   - original research papers;
   - authoritative public records.
4. Use `web_extract` through Firecrawl on promising URLs.
5. Use the built-in browser only when extraction fails or the page needs
   JavaScript, interaction, authentication, or anti-bot handling.
6. Check important claims against another source when practical.
7. Check source dates. For software, prices, policies, model names, and service
   limits, prefer sources with clear current dates.
8. Separate:
   - confirmed fact;
   - inference;
   - recommendation;
   - uncertainty/conflict.
9. Return a short summary. Give the source URL for each important conclusion.

## Source Quality Rules

- Documentation beats blogs for product behavior.
- Source repositories/release notes beat secondary summaries for software.
- A search-result snippet helps you find sources. It does not verify a claim.
- Do not cite a page you did not actually inspect when its contents matter.
- Give less weight to SEO pages, scraped copies, and AI summaries.

## Browser Escalation

Use Firecrawl first. Use the built-in browser second.

Escalate to the built-in browser only when one of these is true:
- extracted content is incomplete or empty;
- you must use navigation to reach the content;
- JavaScript creates the page content;
- a cookie/login session is explicitly required;
- anti-bot behavior blocks normal extraction.

## Handoff

Return these items:
- direct answer;
- key findings;
- important caveats/conflicts;
- source URL per significant claim;
- date/version context where relevant;
- any question that could not be resolved.
