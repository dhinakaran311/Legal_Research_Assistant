"""
Agent 3 — WebResearchAgent  (v2 — P0 async fix)
─────────────────────────────────────────────────
Changes vs v1
  • research_async()  — uses httpx.AsyncClient; IndianKanoon + IndiaCode
    fetched concurrently via asyncio.gather().
  • research()        — sync wrapper; calls asyncio.run(research_async())
    for backward compatibility with existing tests.
  • User-Agent rotated from a pool of 4 strings (harder to fingerprint).
  • asyncio.Semaphore(2) per domain — max 2 concurrent requests.
  • Automatic 1-retry on HTTP 429/503 with 2-second delay.
  • IndiaCode re-enabled behind a flag (was commented out).

Sources (free, no API key):
  1. IndianKanoon (indiankanoon.org)  — case law + statutes
  2. IndiaCode    (indiacode.nic.in)  — official Acts text

After the pipeline stores results into ChromaDB, the SAME query
will hit local on the next call — zero web requests for repeated queries.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# ── User-Agent pool — rotated per request ─────────────────────────────────────
_UA_POOL = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) "
        "Gecko/20100101 Firefox/123.0"
    ),
]
_ua_cycle = itertools.cycle(_UA_POOL)

_BASE_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Referer": "https://www.google.com/",
}

_TIMEOUT  = 12      # seconds per HTTP call
_MAX_DOCS = 6
# Max concurrent requests per domain (polite scraping)
_KANOON_SEM   = asyncio.Semaphore(2)
_INDIACODE_SEM = asyncio.Semaphore(2)


@dataclass
class WebResult:
    title:           str
    url:             str
    content:         str
    web_source:      str        # "indiankanoon" | "indiacode"
    relevance_score: float = 0.65


@dataclass
class WebResearchBundle:
    query:   str
    results: List[WebResult]  = field(default_factory=list)
    error:   Optional[str]    = None

    @property
    def as_documents(self) -> List[Dict[str, Any]]:
        """Same dict shape as LocalResearchAgent documents."""
        docs = []
        for i, r in enumerate(self.results):
            docs.append({
                "id":      f"web_{i}_{abs(hash(r.url)) % 100_000}",
                "content": r.content,
                "excerpt": (r.content[:300] + "...")
                           if len(r.content) > 300 else r.content,
                "metadata": {
                    "source":     "web",
                    "web_source": r.web_source,
                    "url":        r.url,
                    "title":      r.title,
                },
                "relevance_score": r.relevance_score,
                "source": "web",
            })
        return docs


class WebResearchAgent:
    """
    Live-web research agent.

    Requires:
        pip install httpx beautifulsoup4
    Degrades gracefully if libraries are missing.
    """

    def __init__(self, max_docs: int = _MAX_DOCS, timeout: int = _TIMEOUT):
        self.max_docs = max_docs
        self.timeout  = timeout
        self._bs4     = None
        self._load_deps()

    def _load_deps(self) -> None:
        try:
            from bs4 import BeautifulSoup
            self._bs4 = BeautifulSoup
        except ImportError:
            logger.warning("beautifulsoup4 not installed — web search disabled")

    @property
    def available(self) -> bool:
        try:
            import httpx  # noqa: F401
            return self._bs4 is not None
        except ImportError:
            return False

    # ── public API ────────────────────────────────────────────────────────────

    def research(self, query: str, intent: str = "general") -> WebResearchBundle:
        """
        Sync wrapper kept for backward-compatibility (existing tests, non-async callers).
        Internally runs the async version via asyncio.run().
        """
        if not self.available:
            return WebResearchBundle(
                query=query,
                error="Missing: pip install httpx beautifulsoup4",
            )
        try:
            # If already inside an event loop (e.g. pytest-asyncio), use nest_asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Fallback: create a new thread with its own loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(asyncio.run, self.research_async(query, intent))
                    return future.result(timeout=self.timeout * 2 + 5)
            else:
                return asyncio.run(self.research_async(query, intent))
        except Exception as e:
            logger.error("research() failed: %s", e)
            return WebResearchBundle(query=query, error=str(e))

    async def research_async(
        self, query: str, intent: str = "general"
    ) -> WebResearchBundle:
        """
        Async version — IndianKanoon and IndiaCode fetched concurrently.
        The FastAPI route should call this via 'await pipeline.run_async(query)'.
        """
        if not self.available:
            return WebResearchBundle(
                query=query,
                error="Missing: pip install httpx beautifulsoup4",
            )

        import httpx

        async with httpx.AsyncClient(
            headers={**_BASE_HEADERS, "User-Agent": next(_ua_cycle)},
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
        ) as client:
            tasks = [self._search_kanoon_async(client, query)]
            if intent != "case_law":
                tasks.append(self._search_indiacode_async(client, query))

            gathered = await asyncio.gather(*tasks, return_exceptions=True)

        results: List[WebResult] = []
        for item in gathered:
            if isinstance(item, Exception):
                logger.warning("Web source failed: %s", item)
            elif isinstance(item, list):
                results.extend(item)

        # Deduplicate by URL
        seen, deduped = set(), []
        for r in results:
            if r.url not in seen:
                seen.add(r.url)
                deduped.append(r)

        deduped = deduped[: self.max_docs]
        logger.info(
            "WebResearchAgent | %d results for '%s'", len(deduped), query[:70]
        )
        return WebResearchBundle(query=query, results=deduped)

    # ── IndianKanoon (async) ──────────────────────────────────────────────────

    async def _search_kanoon_async(
        self, client, query: str
    ) -> List[WebResult]:
        url = (
            f"https://indiankanoon.org/search/"
            f"?formInput={quote_plus(query)}&pagenum=0"
        )
        logger.debug("Searching IndianKanoon: %s", url)

        async with _KANOON_SEM:
            html = await self._get_async(client, url)

        if not html:
            logger.warning("IndianKanoon: no HTML returned (blocked or 404)")
            return []

        soup, out = self._bs4(html, "html.parser"), []
        for div in soup.select("article.result, div.result")[:5]:
            a_tag = div.select_one(
                "h4.result_title a, a.result_title, div.result_title a, a"
            )
            if not a_tag:
                continue
            title    = a_tag.get_text(strip=True)
            href     = a_tag.get("href", "")
            full_url = (
                f"https://indiankanoon.org{href}"
                if href.startswith("/") else href
            )

            snip_tag = div.select_one(
                "div.headline, div.result_categories, "
                "p.result_snippet, div.snippet, p"
            )
            snippet = snip_tag.get_text(strip=True) if snip_tag else ""

            # Fetch full doc if snippet is empty
            if not snippet and full_url:
                async with _KANOON_SEM:
                    doc_html = await self._get_async(client, full_url)
                snippet = self._extract_kanoon_text(doc_html or "")

            if title and snippet:
                out.append(
                    WebResult(
                        title=title,
                        url=full_url,
                        content=snippet[:1500],
                        web_source="indiankanoon",
                        relevance_score=0.75,
                    )
                )
        return out

    def _extract_kanoon_text(self, html: str) -> str:
        if not html:
            return ""
        soup = self._bs4(html, "html.parser")
        div  = soup.select_one(
            "div#judgments, div.judgments, div#doc_content, article, main"
        )
        if div:
            return re.sub(r"\s{2,}", " ", div.get_text(" ", strip=True))[:1500]
        return ""

    # ── IndiaCode (async) ─────────────────────────────────────────────────────

    async def _search_indiacode_async(
        self, client, query: str
    ) -> List[WebResult]:
        url = f"https://www.indiacode.nic.in/search?query={quote_plus(query)}"
        logger.debug("Searching IndiaCode: %s", url)

        async with _INDIACODE_SEM:
            html = await self._get_async(client, url)

        if not html:
            logger.warning("IndiaCode: no HTML returned (blocked or 404)")
            return []

        soup, out = self._bs4(html, "html.parser"), []
        for card in soup.select(
            "div.card, li.list-group-item, div.result-item"
        )[:4]:
            a_tag = card.select_one("a")
            if not a_tag:
                continue
            title    = a_tag.get_text(strip=True) or "IndiaCode Result"
            href     = a_tag.get("href", "")
            full_url = (
                f"https://www.indiacode.nic.in{href}"
                if href.startswith("/") else href
            )
            desc_tag = card.select_one("p, span, div.description")
            snippet  = desc_tag.get_text(strip=True) if desc_tag else ""
            if not snippet and full_url:
                async with _INDIACODE_SEM:
                    page_html = await self._get_async(client, full_url)
                snippet = self._extract_indiacode_text(page_html or "")
            if title and (snippet or full_url):
                out.append(
                    WebResult(
                        title=title,
                        url=full_url,
                        content=snippet[:1500] if snippet else f"See: {full_url}",
                        web_source="indiacode",
                        relevance_score=0.70,
                    )
                )
        return out

    def _extract_indiacode_text(self, html: str) -> str:
        if not html:
            return ""
        soup = self._bs4(html, "html.parser")
        div  = soup.select_one(
            "div#sectionContent, div.section-content, main, article"
        )
        if div:
            return re.sub(r"\s{2,}", " ", div.get_text(" ", strip=True))[:1500]
        return ""

    # ── Async HTTP helper with 1 retry on 429/503 ─────────────────────────────

    async def _get_async(self, client, url: str) -> Optional[str]:
        """One automatic retry on rate-limit / service unavailable."""
        for attempt in range(2):
            try:
                r = await client.get(
                    url,
                    headers={"User-Agent": next(_ua_cycle)},
                )
                if r.status_code == 200:
                    return r.text
                if r.status_code in (429, 503) and attempt == 0:
                    logger.warning(
                        "HTTP %s for %s — retrying in 2s", r.status_code, url
                    )
                    await asyncio.sleep(2)
                    continue
                logger.warning("HTTP %s for %s", r.status_code, url)
                return None
            except Exception as e:
                logger.error(
                    "GET failed %s — %s: %s", url, type(e).__name__, e
                )
                if attempt == 0:
                    await asyncio.sleep(1)
                    continue
                return None
        return None
