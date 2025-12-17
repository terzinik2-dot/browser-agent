"""
Playwright browser wrapper for Browser Agent.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from config import get_config


class BrowserManager:
    """Manages Playwright browser lifecycle."""

    def __init__(self):
        self.config = get_config()
        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def start(self) -> Page:
        """Start browser and return page."""
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=self.config.headless,
            slow_mo=self.config.slow_mo,
        )

        self.context = await self.browser.new_context(
            viewport={
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            locale="ru-RU",
        )

        self.page = await self.context.new_page()

        # Set default timeout
        self.page.set_default_timeout(self.config.wait_timeout)

        return self.page

    async def stop(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def screenshot(self) -> bytes:
        """Take screenshot of current page."""
        if not self.page:
            raise RuntimeError("Browser not started")

        return await self.page.screenshot(
            type="jpeg",
            quality=self.config.screenshot_quality,
            full_page=False,
        )

    async def wait_for_stable(self):
        """Wait for page to be stable after action."""
        if not self.page:
            return

        try:
            # Wait for network to be idle
            await self.page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass

        # Additional small wait for dynamic content
        await self.page.wait_for_timeout(500)

    def get_url(self) -> str:
        """Get current page URL."""
        if not self.page:
            return ""
        return self.page.url


@asynccontextmanager
async def create_browser() -> AsyncGenerator[BrowserManager, None]:
    """Context manager for browser lifecycle."""
    manager = BrowserManager()
    try:
        await manager.start()
        yield manager
    finally:
        await manager.stop()
