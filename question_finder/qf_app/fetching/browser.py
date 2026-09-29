"""Optional Playwright browser fetcher for JS-rendered pages."""

import hashlib
from qf_app.core.exceptions import FetchError
from qf_app.core.logging import get_logger
from qf_app.fetching.http import FetchResult

logger = get_logger(__name__)


class BrowserFetcher:
    """Optional Playwright headless browser automation for dynamic single-page applications."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def fetch(self, url: str) -> FetchResult:
        """Render page in headless Chromium and return HTML."""
        try:
            from playwright.async_api import async_playwright
        except ImportError as err:
            raise FetchError("Playwright is not installed. Install with: pip install '.[browser]'") from err

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                resp = await page.goto(url, timeout=int(self.timeout * 1000), wait_until="networkidle")
                content = await page.content()
                status_code = resp.status if resp else 200
                await browser.close()

                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                return FetchResult(
                    url=url,
                    final_url=url,
                    status_code=status_code,
                    content_type="text/html",
                    content_length=len(content.encode("utf-8")),
                    content_hash=content_hash,
                    body=content,
                    from_cache=False,
                )
        except Exception as err:
            logger.warning("Browser fetch failed for %s: %s", url, err)
            raise FetchError(f"Browser fetch failed: {err}") from err
