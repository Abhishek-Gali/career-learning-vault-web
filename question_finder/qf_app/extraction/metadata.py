"""HTML metadata extraction: OpenGraph, JSON-LD, and semantic tags."""

import json
from bs4 import BeautifulSoup
from pydantic import BaseModel


class PageMetadata(BaseModel):
    """Extracted page metadata."""

    title: str = ""
    description: str = ""
    author: str = ""
    canonical_url: str = ""
    og_published_time: str | None = None
    og_modified_time: str | None = None
    json_ld_blocks: list[dict] = []
    meta_dates: dict[str, str] = {}


class MetadataExtractor:
    """Parses structural HTML metadata tags."""

    def extract(self, html: str) -> PageMetadata:
        """Extract metadata fields and JSON-LD structured objects."""
        soup = BeautifulSoup(html, "lxml")
        meta = PageMetadata()

        # Title
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            meta.title = title_tag.string.strip()

        # Meta tags
        for tag in soup.find_all("meta"):
            name = tag.get("name", "").lower()
            prop = tag.get("property", "").lower()
            content = tag.get("content", "").strip()

            if not content:
                continue

            if name == "description" or prop == "og:description":
                meta.description = content
            elif name == "author" or prop == "article:author":
                meta.author = content
            elif prop == "article:published_time":
                meta.og_published_time = content
            elif prop == "article:modified_time":
                meta.og_modified_time = content
            elif "date" in name or "time" in name:
                meta.meta_dates[name] = content

        # Canonical Link
        link_canon = soup.find("link", rel="canonical")
        if link_canon and link_canon.get("href"):
            meta.canonical_url = link_canon["href"].strip()

        # JSON-LD Structured Data
        for script in soup.find_all("script", type="application/ld+json"):
            if script.string:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        meta.json_ld_blocks.append(data)
                    elif isinstance(data, list):
                        meta.json_ld_blocks.extend([d for d in data if isinstance(d, dict)])
                except Exception:
                    pass

        return meta
