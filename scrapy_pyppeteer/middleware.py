import asyncio
import logging
from typing import Optional

import pyppeteer
from pyppeteer.browser import Browser
from scrapy.settings import Settings
from twisted.internet.defer import Deferred

from .browser_request import BrowserRequest
from .browser_response import BrowserResponse


logger = logging.getLogger(__name__)


class ScrapyPyppeteerDownloaderMiddleware:
    """ Handles launching browser tabs, acts as a downloader.
    Probably eventually this should be moved to scrapy core as a downloader.
    """
    def __init__(self, settings: Settings):
        self._browser: Optional[Browser] = None
        self._launch_options = settings.getdict('PYPPETEER_LAUNCH') or {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        if isinstance(request, BrowserRequest):
            return _aio_as_deferred(self.process_browser_request(request))
        else:
            return None

    async def process_browser_request(self, request: BrowserRequest):
        if self._browser is None:
            self._browser = await pyppeteer.launch(**self._launch_options)
        page = await self._browser.newPage()
        n_tabs = _n_browser_tabs(self._browser)
        logger.debug(f'{n_tabs} tabs open')
        if request.is_blank:
            url = request.url
        else:
            await page.goto(request.url)
            url = page.url
            # TODO set status and headers
        return BrowserResponse(url=url, browser_tab=page)


def _n_browser_tabs(browser: Browser) -> int:
    """ A quick way to get the number of browser tabs.
    """
    n_tabs = 0
    for context in browser.browserContexts:
        for target in context.targets():
            if target.type == 'page':
                n_tabs += 1
    return n_tabs


def _aio_as_deferred(f):
    return Deferred.fromFuture(asyncio.ensure_future(f))
