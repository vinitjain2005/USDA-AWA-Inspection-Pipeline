"""
Selenium scraper for USDA APHIS Public Search Tool inspection PDFs.

Flow on the inspection-reports page: set filters → Submit → results show PDF links
(usually at the top). This script clicks each PDF link (or opens the URL) so Chrome
saves files into data/raw_pdfs/, then moves to the next page if present.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

from selenium import webdriver
from selenium.common.exceptions import (
    JavascriptException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

DEFAULT_URL = "https://aphis.my.site.com/PublicSearchTool/s/inspection-reports"
DEFAULT_WAIT_SEC = 25
BETWEEN_CLICKS_SEC = 2.0
AFTER_DOWNLOAD_SEC = 2.5


def _is_http_navigable(href: str) -> bool:
    if not href:
        return False
    h = href.strip()
    if h.startswith("#") or h.lower().startswith("javascript:"):
        return False
    parsed = urlparse(h)
    if parsed.scheme in ("mailto", "tel", "data", "file", "javascript"):
        return False
    return parsed.scheme in ("http", "https") or (
        not parsed.scheme and bool(parsed.path or parsed.netloc)
    )


def _normalize_url(href: str, base_url: str) -> str:
    h = href.strip()
    if urlparse(h).scheme in ("http", "https"):
        return h
    return urljoin(base_url, h)


def _urls_equivalent(a: str, b: str, base: str) -> bool:
    return _normalize_url(a, base).rstrip("/") == _normalize_url(b, base).rstrip("/")


def _looks_like_pdf_href(href: str) -> bool:
    """True if this anchor likely downloads or opens a PDF."""
    if not _is_http_navigable(href):
        return False
    low = unquote(href).lower()
    path = low.split("?", 1)[0]
    if path.endswith(".pdf") or ".pdf?" in low:
        return True
    if "format=pdf" in low or "contenttype=application%2fpdf" in low.replace(" ", ""):
        return True
    if "/servlet/" in low and "pdf" in low:
        return True
    return False


class USDAScraper:
    def __init__(
        self,
        download_dir: Path | str,
        base_url: str = DEFAULT_URL,
        headless: bool = False,
    ) -> None:
        self.download_dir = Path(download_dir).resolve()
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url
        self.headless = headless
        self.driver: webdriver.Chrome | None = None

    def _build_driver(self) -> webdriver.Chrome:
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1400,900")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        prefs = {
            "download.default_directory": str(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        }
        opts.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        driver.set_page_load_timeout(DEFAULT_WAIT_SEC)
        driver.implicitly_wait(3)
        return driver

    def start(self) -> None:
        if self.driver is None:
            self.driver = self._build_driver()

    def stop(self) -> None:
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    def wait_after_submit(self) -> None:
        """Wait until results (with PDF links) are visible; user drives Submit in the UI."""
        input(
            "\nIn the browser: set your filters, click **Submit**, wait until results appear "
            "(PDF links are usually at the top). Then press **Enter** here to download those PDFs.\n"
        )

    def _safe_click(self, element) -> bool:
        assert self.driver is not None
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'start', inline: 'nearest'});",
                element,
            )
            time.sleep(0.2)
        except WebDriverException:
            pass
        try:
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except JavascriptException:
            try:
                ActionChains(self.driver).move_to_element(element).pause(0.1).click().perform()
                return True
            except WebDriverException:
                return False

    def _collect_pdf_hrefs_on_page(self) -> list[str]:
        """Collect unique PDF URLs from the current results view (anchors at top of results)."""
        assert self.driver is not None
        base = self.driver.current_url
        seen: set[str] = set()
        ordered: list[str] = []
        for el in self.driver.find_elements(By.CSS_SELECTOR, "a[href]"):
            href = (el.get_attribute("href") or "").strip()
            if not href or not _looks_like_pdf_href(href):
                continue
            norm = _normalize_url(href, base)
            if norm in seen:
                continue
            seen.add(norm)
            ordered.append(norm)
        return ordered

    def _return_to_results(self, list_url: str) -> None:
        assert self.driver is not None
        try:
            if self.driver.current_url.rstrip("/") != list_url.rstrip("/"):
                self.driver.get(list_url)
                time.sleep(1.0)
        except WebDriverException as e:
            logger.warning("Could not return to results page: %s", e)

    def _download_one_pdf(self, list_url: str, href: str) -> None:
        """
        Prefer clicking the same <a> the user would click; fallback to GET(href).
        Always end on list_url so the next PDF link can be found.
        """
        assert self.driver is not None
        self._return_to_results(list_url)

        clicked = False
        for el in self.driver.find_elements(By.CSS_SELECTOR, "a[href]"):
            try:
                raw = (el.get_attribute("href") or "").strip()
                if raw and _urls_equivalent(raw, href, list_url):
                    if self._safe_click(el):
                        clicked = True
                    break
            except StaleElementReferenceException:
                continue

        if not clicked:
            logger.info("Opening PDF URL directly (no matching anchor clicked)")
            self.driver.get(href)

        time.sleep(AFTER_DOWNLOAD_SEC)
        self._return_to_results(list_url)

    def _click_next_page(self) -> bool:
        assert self.driver is not None
        for xpath in (
            "//a[contains(., 'Next')]",
            "//button[contains(., 'Next')]",
            "//a[@aria-label='Next']",
        ):
            try:
                nxt = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                clicked = self._safe_click(nxt)
                if not clicked:
                    try:
                        nxt.click()
                        clicked = True
                    except JavascriptException:
                        pass
                if clicked:
                    time.sleep(BETWEEN_CLICKS_SEC)
                    return True
            except (TimeoutException, StaleElementReferenceException):
                continue
        return False

    def run(self, max_pages: int | None = None) -> None:
        """
        After you submit the search: for each results page, find PDF links (typically
        at the top), click/open each to download, then go to Next if available.
        """
        self.start()
        assert self.driver is not None
        try:
            logger.info("Opening %s", self.base_url)
            self.driver.get(self.base_url)
            self.wait_after_submit()

            page = 1
            while True:
                list_url = self.driver.current_url
                logger.info("Results page %s — scanning for PDF links (current URL logged)", page)

                pdf_hrefs = self._collect_pdf_hrefs_on_page()
                logger.info("Found %s PDF link(s) on this page", len(pdf_hrefs))

                for i, href in enumerate(pdf_hrefs, start=1):
                    short = href if len(href) < 100 else href[:97] + "..."
                    logger.info("  [%s/%s] %s", i, len(pdf_hrefs), short)
                    try:
                        self._download_one_pdf(list_url, href)
                    except WebDriverException as e:
                        logger.warning("Skipped PDF due to error: %s", e)
                        self._return_to_results(list_url)

                if max_pages is not None and page >= max_pages:
                    logger.info("Stopped after max_pages=%s", max_pages)
                    break
                if not self._click_next_page():
                    logger.info("No Next page — done.")
                    break
                page += 1
        finally:
            self.stop()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    root = Path(__file__).resolve().parents[1]
    out = root / "data" / "raw_pdfs"
    scraper = USDAScraper(download_dir=out)
    scraper.run()


if __name__ == "__main__":
    main()
