"""
Agent 3 — WebResearchAgent
───────────────────────────
Scrapes live Indian legal sources when local DB is insufficient.

Sources (free, no API key):
  1. IndianKanoon (indiankanoon.org)  — case law + statutes
  2. IndiaCode    (indiacode.nic.in)  — official Acts text

After the pipeline stores results into ChromaDB, the SAME query
will hit local on the next call — zero web requests for repeated queries.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_TIMEOUT  = 12
_MAX_DOCS = 6


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
    Requires: pip install requests beautifulsoup4
    Degrades gracefully if libraries are missing.
    """

    def __init__(self, max_docs: int = _MAX_DOCS, timeout: int = _TIMEOUT):
        self.max_docs = max_docs
        self.timeout  = timeout
        self._req     = None
        self._bs4     = None
        self._load_deps()

    def _load_deps(self) -> None:
        try:
            import requests
            self._req = requests
        except ImportError:
            logger.warning("requests not installed — web search disabled")
        try:
            from bs4 import BeautifulSoup
            self._bs4 = BeautifulSoup
        except ImportError:
            logger.warning("beautifulsoup4 not installed — web search disabled")

    @property
    def available(self) -> bool:
        return self._req is not None and self._bs4 is not None

    # ── public API ────────────────────────────────────────────────────────────

    def research(self, query: str, intent: str = "general") -> WebResearchBundle:
        if not self.available:
            return WebResearchBundle(
                query=query,
                error="Missing: pip install requests beautifulsoup4",
            )

        results: List[WebResult] = []

        # IndianKanoon — best for case law AND statute sections
        try:
            results.extend(self._search_kanoon(query)[:3])
        except Exception as e:
            logger.warning("IndianKanoon failed: %s", e)

        # IndiaCode — best for full statute text (skip for pure case_law)
        if intent != "case_law" and len(results) < self.max_docs:
            try:
                results.extend(self._search_indiacode(query)[:3])
            except Exception as e:
                logger.warning("IndiaCode failed: %s", e)

        # deduplicate by URL
        seen, deduped = set(), []
        for r in results:
            if r.url not in seen:
                seen.add(r.url)
                deduped.append(r)

        deduped = deduped[: self.max_docs]
        logger.info("WebResearchAgent | %d results for '%s'",
                    len(deduped), query[:70])
        return WebResearchBundle(query=query, results=deduped)

    # ── IndianKanoon ──────────────────────────────────────────────────────────

    def _search_kanoon(self, query: str) -> List[WebResult]:
        url  = (f"https://indiankanoon.org/search/"
                f"?formInput={quote_plus(query)}&pagenum=0")
        html = self._get(url)
        if not html:
            return []

        soup, out = self._bs4(html, "html.parser"), []
        for div in soup.select("div.result")[:5]:
            a_tag = div.select_one("a.result_title, div.result_title a, a")
            if not a_tag:
                continue
            title    = a_tag.get_text(strip=True)
            href     = a_tag.get("href", "")
            full_url = (f"https://indiankanoon.org{href}"
                        if href.startswith("/") else href)

            snip_tag = div.select_one(
                "div.result_categories, p.result_snippet, div.snippet, p"
            )
            snippet = snip_tag.get_text(strip=True) if snip_tag else ""

            # fetch full doc if snippet is empty
            if not snippet and full_url:
                snippet = self._fetch_kanoon_doc(full_url)

            if title and snippet:
                out.append(WebResult(
                    title=title, url=full_url,
                    content=snippet[:1500],
                    web_source="indiankanoon",
                    relevance_score=0.75,
                ))
        return out

    def _fetch_kanoon_doc(self, url: str) -> str:
        html = self._get(url)
        if not html:
            return ""
        soup = self._bs4(html, "html.parser")
        div  = soup.select_one(
            "div#judgments, div.judgments, div#doc_content, article, main"
        )
        if div:
            return re.sub(r"\s{2,}", " ", div.get_text(" ", strip=True))[:1500]
        return ""

    # ── IndiaCode ─────────────────────────────────────────────────────────────

    def _search_indiacode(self, query: str) -> List[WebResult]:
        url  = (f"https://www.indiacode.nic.in/search"
                f"?query={quote_plus(query)}")
        html = self._get(url)
        if not html:
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
            full_url = (f"https://www.indiacode.nic.in{href}"
                        if href.startswith("/") else href)
            desc_tag = card.select_one("p, span, div.description")
            snippet  = desc_tag.get_text(strip=True) if desc_tag else ""
            if not snippet:
                snippet = self._fetch_indiacode_page(full_url)
            if title and (snippet or full_url):
                out.append(WebResult(
                    title=title, url=full_url,
                    content=snippet[:1500] if snippet else f"See: {full_url}",
                    web_source="indiacode",
                    relevance_score=0.70,
                ))
        return out

    def _fetch_indiacode_page(self, url: str) -> str:
        html = self._get(url)
        if not html:
            return ""
        soup = self._bs4(html, "html.parser")
        div  = soup.select_one(
            "div#sectionContent, div.section-content, main, article"
        )
        if div:
            return re.sub(r"\s{2,}", " ", div.get_text(" ", strip=True))[:1500]
        return ""

    # ── HTTP helper ───────────────────────────────────────────────────────────

    def _get(self, url: str) -> Optional[str]:
        try:
            r = self._req.get(url, headers=_HEADERS, timeout=self.timeout)
            if r.status_code == 200:
                return r.text
            logger.debug("HTTP %s for %s", r.status_code, url)
        except Exception as e:
            logger.debug("GET failed %s — %s", url, e)
        return None
