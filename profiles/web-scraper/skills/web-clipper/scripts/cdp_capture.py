#!/usr/bin/env python3
"""Direct Chrome DevTools Protocol client for headless Chromium capture.

Use when ``browser_exec`` cannot auto-launch Chrome (e.g. Playwright Chromium
is installed at a non-default path) or the installed ``browser-use`` CLI does
not expose a ``browser_helpers`` module. Requires only the ``websockets``
package; no Playwright/Selenium/Puppeteer dependency.

This is a *library*, not a CLI. Import :func:`capture_url` from a one-off
script that loops over a list of pages and writes Markdown notes.

Usage example
-------------
Run a headless Chromium in the background first::

    /home/ubuntu/.cache/ms-playwright/chromium-1243/chrome-linux-arm64/chrome \\
      --headless=new --no-sandbox --disable-gpu \\
      --remote-debugging-address=127.0.0.1 --remote-debugging-port=9224 \\
      --user-data-dir=/tmp/cdp-clip-browser about:blank

Then in Python::

    from cdp_capture import capture_url
    payload = capture_url(9224, "https://example.com/docs/page")
    print(payload["title"], payload["canonical"])
    print(payload["body"][:500])

The returned ``payload`` is a dict with ``title``, ``canonical``, ``desc``,
``headings``, ``tables`` (list of Markdown tables), and ``body`` (cleaned
Markdown body — headings, paragraphs, lists, and tables in document order;
no cookie banners, no nav, no footers).
"""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Any

import websockets.sync.client as ws_sync  # type: ignore


# Selectors that almost never carry article content. Stripped before
# TreeWalker so the cleaned body does not contain "Accept all / Confirm
# choices / Close" lines from a cookie consent dialog.
NOISE_SELECTORS = [
    "script", "style", "noscript", "svg", "button",
    "nav", "header", "footer", "aside",
    "[role=dialog]", "[aria-modal=true]",
    "[data-testid*=consent]", "[id*=cookie]", "[class*=cookie]",
    "[class*=consent]", "[class*=banner]", "[class*=popup]",
    "[class*=overlay]", "[class*=paywall]", "[class*=newsletter]",
]


# JavaScript that runs inside the page. Returns JSON with title, canonical,
# description, headings, tables (Markdown), and body (cleaned Markdown).
EXTRACT_JS = r"""
(() => {
  document.querySelectorAll(%s).forEach(n => n.remove());
  const root = document.querySelector('article, main, .prose, [role=main], body') || document.body;
  const title = (document.querySelector('h1') || {}).innerText || document.title || '';
  const canonical = document.querySelector('link[rel=canonical]')?.href || location.href;
  const desc = document.querySelector('meta[name=description]')?.content || '';
  const headings = Array.from(root.querySelectorAll('h1,h2,h3,h4')).map(h =>
    '#'.repeat(parseInt(h.tagName[1])) + ' ' + h.innerText.trim()
  );
  const tables = Array.from(root.querySelectorAll('table')).map(t => {
    const rows = Array.from(t.querySelectorAll('tr')).map(tr =>
      Array.from(tr.querySelectorAll('th,td')).map(c => c.innerText.trim().replace(/\s+/g,' '))
    );
    const header = rows.shift() || [];
    const lines = ['| ' + header.join(' | ') + ' |', '|' + header.map(()=> '---').join('|') + '|'];
    for (const r of rows) { if (r.length) lines.push('| ' + r.join(' | ') + ' |'); }
    return lines.join('\n');
  });
  const tableSet = new Set(Array.from(root.querySelectorAll('table')));
  let tableIdx = 0;
  const body = [];
  // Walk elements in document order so tables stay among their surrounding text.
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null);
  let node = walker.currentNode;
  while (node) {
    if (node.nodeType === 1) {
      const tag = node.tagName.toLowerCase();
      if (tableSet.has(node)) {
        body.push('\n\n' + (tables[tableIdx] || '') + '\n\n');
        tableIdx++;
        // The table Markdown is already emitted; skip its descendants to avoid duplicates.
        let sib = walker.nextSibling();
        if (!sib) { const p = walker.parentNode(); sib = p ? walker.nextSibling() : null; }
        node = sib;
        continue;
      }
      if (/^h[1-6]$/.test(tag)) {
        const txt = (node.innerText || '').trim();
        if (txt) body.push('\n\n' + '#'.repeat(Math.min(6, parseInt(tag[1]) + 1)) + ' ' + txt + '\n\n');
      } else if (tag === 'p') {
        const txt = (node.innerText || '').replace(/\s+/g, ' ').trim();
        if (txt) body.push('\n\n' + txt + '\n\n');
      } else if (tag === 'ul' || tag === 'ol') {
        const items = Array.from(node.children).map(li => {
          const t = (li.innerText || '').trim();
          if (!t) return '';
          if (tag === 'ol') return (Array.prototype.indexOf.call(node.children, li) + 1) + '. ' + t;
          return '- ' + t;
        }).filter(Boolean);
        if (items.length) body.push('\n\n' + items.join('\n') + '\n\n');
      } else if (tag === 'blockquote') {
        const txt = (node.innerText || '').trim();
        if (txt) body.push('\n\n' + txt.split('\n').map(x => '> ' + x).join('\n') + '\n\n');
      }
    }
    node = walker.nextNode();
  }
  return JSON.stringify({title, canonical, desc, headings, tables, body: body.join('')});
})()
""" % json.dumps(",".join(NOISE_SELECTORS))


def _http_json(method: str, path: str) -> dict:
    # Chromium exposes tab creation and cleanup through its local JSON endpoint.
    req = urllib.request.Request(f"http://127.0.0.1:{path}", method=method)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def capture_url(cdp_port: int, url: str, *, load_timeout: float = 30.0) -> dict[str, Any]:
    """Open ``url`` in a fresh Chromium tab on ``cdp_port`` and return the
    extracted payload as a dict.

    The tab is closed before returning. The function blocks until either
    ``Page.loadEventFired`` is observed or ``load_timeout`` elapses.
    """
    target = _http_json("PUT", f"/json/new?about:blank")
    ws_url = target["webSocketDebuggerUrl"]
    try:
        with ws_sync.connect(ws_url, max_size=64 * 1024 * 1024) as ws:
            # Enable the page and JavaScript domains before navigating, so events
            # and the later extraction command are available on this connection.
            ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
            ws.send(json.dumps({"id": 2, "method": "Runtime.enable"}))
            ws.send(json.dumps({"id": 3, "method": "Page.navigate", "params": {"url": url}}))
            deadline = time.time() + load_timeout
            while time.time() < deadline:
                try:
                    msg = json.loads(ws.recv(timeout=3))
                except Exception:
                    continue
                # CDP also sends replies to our commands; wait specifically for load.
                if msg.get("method") == "Page.loadEventFired":
                    break
            time.sleep(1.5)
            ws.send(json.dumps({
                "id": 4,
                "method": "Runtime.evaluate",
                "params": {"expression": EXTRACT_JS, "returnByValue": True, "awaitPromise": True},
            }))
            deadline = time.time() + 15
            value = ""
            while time.time() < deadline:
                try:
                    msg = json.loads(ws.recv(timeout=3))
                except Exception:
                    continue
                if msg.get("id") == 4:
                    value = msg.get("result", {}).get("result", {}).get("value", "")
                    break
        if not value:
            raise RuntimeError(f"empty payload for {url}")
        return json.loads(value)
    finally:
        # Close the temporary tab even when navigation or extraction fails.
        try:
            _http_json("PUT", f"/json/close/{target.get('id')}")
        except Exception:
            pass
