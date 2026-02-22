"""MCP resources exposing Stream documentation for agent reference.

Documentation pages are **auto-discovered** from the Stream docs sitemap
(https://docs.streampay.sa/sitemap.xml).  API-reference pages (``/api/…``)
are excluded because they are already covered by the OpenAPI spec resource.

All fetched content is cached in-memory for 1 hour.
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlparse

import httpx
from fastmcp import FastMCP

from stream_mcp.config import settings

logger = logging.getLogger(__name__)

_DOCS_BASE = settings.stream_docs_url.rstrip("/")
_SITEMAP_URL = f"{_DOCS_BASE}/sitemap.xml"
_OPENAPI_URL = f"{_DOCS_BASE}/openapi.json"
_CACHE_TTL = 3600  # 1 hour

# ── caches ────────────────────────────────────────────────────────────
_openapi_cache: str | None = None
_openapi_cache_at: float = 0.0

_page_cache: dict[str, tuple[str, float]] = {}  # slug → (html, timestamp)

_sitemap_pages: dict[str, str] | None = None  # slug → full URL
_sitemap_fetched_at: float = 0.0

# Pages to skip (not useful as standalone docs for agents)
_SKIP_PATHS: set[str] = {"/", "/api", "/search", "/LLMS_TESTING"}


# ── helpers ───────────────────────────────────────────────────────────
def _url_to_slug(url: str) -> str:
    """Convert a full URL to a slug, e.g. /sdks/express → sdks-express."""
    path = urlparse(url).path.rstrip("/")
    return path.lstrip("/").replace("/", "-")


async def _fetch_sitemap() -> dict[str, str]:
    """Fetch and parse the sitemap, returning {slug: url} for doc pages."""
    global _sitemap_pages, _sitemap_fetched_at

    now = time.time()
    if _sitemap_pages is not None and (now - _sitemap_fetched_at) < _CACHE_TTL:
        return _sitemap_pages

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as http:
            r = await http.get(_SITEMAP_URL)
            r.raise_for_status()

        root = ET.fromstring(r.text)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        pages: dict[str, str] = {}
        for url_el in root.findall("s:url/s:loc", ns):
            loc = url_el.text
            if not loc:
                continue
            path = urlparse(loc).path.rstrip("/") or "/"
            # Skip API reference pages & utility pages
            if path in _SKIP_PATHS or path.startswith("/api/"):
                continue
            slug = _url_to_slug(loc)
            if slug:
                pages[slug] = loc

        _sitemap_pages = pages
        _sitemap_fetched_at = time.time()
        logger.info(
            "Discovered %d doc pages from sitemap: %s",
            len(pages),
            ", ".join(sorted(pages.keys())),
        )
        return _sitemap_pages

    except Exception as exc:
        logger.warning("Failed to fetch sitemap: %s", exc)
        if _sitemap_pages is not None:
            return _sitemap_pages  # serve stale
        return {}


async def _fetch_page(url: str, slug: str) -> str:
    """Fetch a page's HTML and cache it."""
    now = time.time()
    if slug in _page_cache:
        html, cached_at = _page_cache[slug]
        if (now - cached_at) < _CACHE_TTL:
            return html

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as http:
            r = await http.get(url)
            r.raise_for_status()
            html = r.text
            _page_cache[slug] = (html, time.time())
            logger.info("Cached doc page '%s' from %s", slug, url)
            return html
    except Exception as exc:
        logger.warning("Failed to fetch page %s: %s", url, exc)
        if slug in _page_cache:
            return _page_cache[slug][0]
        return f'{{"error": "Page unavailable", "slug": "{slug}", "detail": "{exc}"}}'


# ── registration ──────────────────────────────────────────────────────
def register(mcp: FastMCP) -> None:
    """Register all Stream documentation resources and tools on *mcp*."""

    # ── OpenAPI spec resource ─────────────────────────────────────────
    @mcp.resource("stream://docs/openapi", mime_type="application/json")
    async def get_openapi_spec() -> str:
        """Returns the full Stream OpenAPI JSON spec for agent reference.

        Fetched from https://docs.streampay.sa/openapi.json and cached for 1 hour.
        """
        global _openapi_cache, _openapi_cache_at

        now = time.time()
        if _openapi_cache and (now - _openapi_cache_at) < _CACHE_TTL:
            return _openapi_cache

        try:
            async with httpx.AsyncClient(timeout=15) as http:
                r = await http.get(_OPENAPI_URL)
                r.raise_for_status()
                _openapi_cache = r.text
                _openapi_cache_at = time.time()
                logger.info("Refreshed OpenAPI spec cache from %s", _OPENAPI_URL)
                return _openapi_cache
        except Exception as exc:
            logger.warning("Failed to fetch OpenAPI spec: %s", exc)
            if _openapi_cache:
                return _openapi_cache
            return '{"error": "OpenAPI spec unavailable", "detail": "' + str(exc) + '"}'

    # ── Doc page resource template ────────────────────────────────────
    @mcp.resource("stream://docs/pages/{slug}", mime_type="text/html")
    async def get_docs_page(slug: str) -> str:
        """Returns the HTML content of a Stream documentation page by slug.

        Slugs are auto-discovered from the sitemap. Use the list_stream_docs
        tool to see all available slugs.
        """
        pages = await _fetch_sitemap()
        if slug not in pages:
            available = ", ".join(sorted(pages.keys()))
            return f'{{"error": "Unknown slug \\"{slug}\\". Available: {available}"}}'
        return await _fetch_page(pages[slug], slug)

    # ── Tool: list available doc pages ────────────────────────────────
    @mcp.tool()
    async def list_stream_docs() -> dict[str, Any]:
        """List all available Stream documentation pages.

        Pages are auto-discovered from the Stream docs sitemap.
        Returns slug, URL, and resource URI for each page.
        Use the slug with get_stream_doc to fetch the full content.
        """
        pages = await _fetch_sitemap()
        result = []
        for slug in sorted(pages.keys()):
            result.append({
                "slug": slug,
                "url": pages[slug],
                "resource_uri": f"stream://docs/pages/{slug}",
            })
        return {"pages": result, "total": len(result)}

    # ── Tool: fetch a single doc page ─────────────────────────────────
    @mcp.tool()
    async def get_stream_doc(slug: str) -> dict[str, Any]:
        """Fetch the content of a Stream documentation page by slug.

        Slugs are auto-discovered from the sitemap. Call list_stream_docs
        first to see what's available, or pass a slug directly if you
        already know it (e.g. 'getting-started', 'testing-cards',
        'webhooks', 'authentication', etc.).
        """
        pages = await _fetch_sitemap()
        if slug not in pages:
            available = sorted(pages.keys())
            return {"error": f"Unknown slug '{slug}'", "available_slugs": available}

        url = pages[slug]
        content = await _fetch_page(url, slug)
        return {"slug": slug, "url": url, "content": content}
