"""Content-addressed local page caching."""

import hashlib
import json
from pathlib import Path
from pydantic import BaseModel
from qf_app.core.paths import PAGE_CACHE_DIR


class CachedPage(BaseModel):
    """Cached page payload with HTTP headers and body."""

    url: str
    status_code: int
    content_type: str
    headers: dict[str, str]
    body: str
    content_hash: str
    etag: str | None = None
    last_modified: str | None = None


class PageCacheManager:
    """Manages disk-based content-addressed HTML caching in data/cache/pages/."""

    def __init__(self, cache_dir: Path = PAGE_CACHE_DIR) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_url_hash(self, url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def get(self, url: str) -> CachedPage | None:
        """Retrieve cached page if available."""
        url_hash = self._get_url_hash(url)
        page_file = self.cache_dir / f"{url_hash}.json"
        if page_file.exists():
            try:
                data = json.loads(page_file.read_text(encoding="utf-8"))
                return CachedPage(**data)
            except Exception:
                return None
        return None

    def store(
        self,
        url: str,
        status_code: int,
        content_type: str,
        headers: dict[str, str],
        body: str,
    ) -> CachedPage:
        """Store fetched page into cache."""
        url_hash = self._get_url_hash(url)
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        cached = CachedPage(
            url=url,
            status_code=status_code,
            content_type=content_type,
            headers=headers,
            body=body,
            content_hash=content_hash,
            etag=headers.get("etag"),
            last_modified=headers.get("last-modified"),
        )

        page_file = self.cache_dir / f"{url_hash}.json"
        page_file.write_text(cached.model_dump_json(indent=2), encoding="utf-8")
        return cached
