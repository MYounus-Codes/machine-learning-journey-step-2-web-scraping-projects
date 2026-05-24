"""
Amazon Gaming Keyboard Scraper
================================
Robust, human-like scraper using Playwright.
Collects: product name, price, original price, discount %, rating, image URL.
Saves results to amazon_gaming_keyboards.csv
"""

import csv
import random
import time
import logging
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("amazon-scraper")

# ── Config ────────────────────────────────────────────────────────────────────
START_URL = (
    "https://www.amazon.com/s?k=best+gaming+keyboard"
    "&crid=346Z7KIL7KAJP"
    "&sprefix=best+gaming+keyboard%2Caps%2C680"
    "&ref=nb_sb_ss_p13n-expert-pd-ops-ranker_1_20"
)
MAX_PAGES   = 5          # how many result pages to scrape
OUTPUT_FILE = "amazon_gaming_keyboards.csv"
HEADLESS    = True       # set False to watch the browser


# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class Product:
    name:           str  = ""
    current_price:  str  = ""
    original_price: str  = ""
    discount_pct:   str  = ""
    rating:         str  = ""
    review_count:   str  = ""
    image_url:      str  = ""
    product_url:    str  = ""


# ── Human-like helpers ────────────────────────────────────────────────────────
def _sleep(lo: float = 1.5, hi: float = 3.5) -> None:
    """Random pause to mimic human reading speed."""
    delay = random.uniform(lo, hi)
    log.debug("Sleeping %.1fs", delay)
    time.sleep(delay)


def _human_scroll(page: Page) -> None:
    """Scroll the page in small, irregular increments."""
    total   = random.randint(1800, 3200)
    scrolled = 0
    while scrolled < total:
        step = random.randint(150, 400)
        page.mouse.wheel(0, step)
        scrolled += step
        time.sleep(random.uniform(0.08, 0.22))


def _move_mouse_randomly(page: Page) -> None:
    """Move the mouse to a random position on the viewport."""
    vw = page.viewport_size or {"width": 1280, "height": 900}
    x  = random.randint(100, vw["width"]  - 100)
    y  = random.randint(100, vw["height"] - 100)
    page.mouse.move(x, y, steps=random.randint(5, 15))


# ── Browser factory ───────────────────────────────────────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
    "Gecko/20100101 Firefox/125.0",
]


def _launch_browser(p) -> tuple[Browser, object]:
    ua = random.choice(_USER_AGENTS)
    browser = p.chromium.launch(
        headless=HEADLESS,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-infobars",
            "--window-size=1280,900",
        ],
    )
    context = browser.new_context(
        user_agent=ua,
        viewport={"width": 1280, "height": 900},
        locale="en-US",
        timezone_id="America/New_York",
        java_script_enabled=True,
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer":         "https://www.google.com/",
            "DNT":             "1",
        },
    )
    # Hide webdriver fingerprint
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    """)
    page = context.new_page()
    return browser, page


# ── Parsing ───────────────────────────────────────────────────────────────────
def _parse_products(html: str) -> list[Product]:
    soup  = BeautifulSoup(html, "html.parser")
    cards = soup.select(
        "div[data-component-type='s-search-result']"
    )
    products: list[Product] = []

    for card in cards:
        p = Product()

        # ── Name ──────────────────────────────────────────────────────────────
        name_el = card.select_one("h2 span")
        if not name_el:
            continue                        # skip sponsored / non-product rows
        p.name = name_el.get_text(strip=True)

        # ── Current price ─────────────────────────────────────────────────────
        price_whole = card.select_one(".a-price .a-price-whole")
        price_frac  = card.select_one(".a-price .a-price-fraction")
        if price_whole:
            frac = price_frac.get_text(strip=True) if price_frac else "00"
            p.current_price = f"${price_whole.get_text(strip=True).rstrip('.')}.{frac}"

        # ── Original / list price ─────────────────────────────────────────────
        original_el = card.select_one(
            ".a-price.a-text-price span.a-offscreen"
        )
        if original_el:
            p.original_price = original_el.get_text(strip=True)

        # ── Discount % ────────────────────────────────────────────────────────
        discount_el = card.select_one(".a-badge-text")
        if not discount_el:
            discount_el = card.select_one(
                "span:-soup-contains('% off')"
            )
        if discount_el:
            p.discount_pct = discount_el.get_text(strip=True)
        elif p.current_price and p.original_price:
            # Compute it ourselves if both prices are available
            try:
                cur  = float(p.current_price.replace("$", "").replace(",", ""))
                orig = float(p.original_price.replace("$", "").replace(",", ""))
                if orig > cur:
                    pct = round((orig - cur) / orig * 100)
                    p.discount_pct = f"{pct}% off"
            except ValueError:
                pass

        # ── Rating ────────────────────────────────────────────────────────────
        rating_el = card.select_one("span[aria-label*='out of 5 stars']")
        if rating_el:
            p.rating = rating_el["aria-label"].split(" ")[0]

        # ── Review count ──────────────────────────────────────────────────────
        reviews_el = card.select_one("span[aria-label*='stars'] + span a span")
        if not reviews_el:
            reviews_el = card.select_one(".a-size-base.s-underline-text")
        if reviews_el:
            p.review_count = reviews_el.get_text(strip=True)

        # ── Image URL ─────────────────────────────────────────────────────────
        img_el = card.select_one("img.s-image")
        if img_el:
            p.image_url = img_el.get("src", "")

        # ── Product URL ───────────────────────────────────────────────────────
        link_el = card.select_one("a.a-link-normal.s-no-outline")
        if link_el:
            href = link_el.get("href", "")
            p.product_url = (
                f"https://www.amazon.com{href}"
                if href.startswith("/")
                else href
            )

        products.append(p)

    return products


# ── CSV writer ────────────────────────────────────────────────────────────────
def _save_csv(products: list[Product], path: str) -> None:
    fieldnames = [f.name for f in fields(Product)]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for prod in products:
            writer.writerow(
                {k: getattr(prod, k) for k in fieldnames}
            )
    log.info("Saved %d products → %s", len(products), path)


# ── Main scraper ──────────────────────────────────────────────────────────────
def scrape() -> list[Product]:
    all_products: list[Product] = []

    with sync_playwright() as p:
        browser, page = _launch_browser(p)

        try:
            log.info("Navigating to Amazon search page …")
            page.goto(START_URL, wait_until="domcontentloaded", timeout=30_000)
            _sleep(2, 4)

            for page_num in range(1, MAX_PAGES + 1):
                log.info("── Scraping page %d ──", page_num)

                # Wait for product cards to appear
                page.wait_for_selector(
                    "div[data-component-type='s-search-result']",
                    timeout=15_000,
                )

                # Simulate human behaviour on the page
                _move_mouse_randomly(page)
                _human_scroll(page)
                _move_mouse_randomly(page)
                _sleep(1.0, 2.5)

                html      = page.content()
                products  = _parse_products(html)
                all_products.extend(products)
                log.info("  Found %d products on this page", len(products))

                # ── Next page ─────────────────────────────────────────────────
                if page_num >= MAX_PAGES:
                    break

                next_btn = page.query_selector(
                    "a.s-pagination-item.s-pagination-next:not(.s-pagination-disabled)"
                )
                if not next_btn:
                    log.info("No 'Next' button — reached last page.")
                    break

                # Scroll button into view, hover, then click (human-like)
                next_btn.scroll_into_view_if_needed()
                _sleep(0.5, 1.2)
                next_btn.hover()
                _sleep(0.3, 0.8)
                next_btn.click()

                page.wait_for_load_state("domcontentloaded")
                _sleep(2.5, 5.0)

        except Exception as exc:
            log.error("Scraping error: %s", exc)
            raise
        finally:
            browser.close()

    log.info("Total products collected: %d", len(all_products))
    return all_products


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    products = scrape()

    if products:
        _save_csv(products, OUTPUT_FILE)
        # Quick preview
        print(f"\n{'─'*80}")
        print(f"{'PRODUCT':<50} {'PRICE':>8}  {'DISC':>8}  {'RATING':>6}")
        print(f"{'─'*80}")
        for prod in products[:10]:
            name = prod.name[:47] + "…" if len(prod.name) > 48 else prod.name
            print(
                f"{name:<50} {prod.current_price:>8}  "
                f"{prod.discount_pct:>8}  {prod.rating:>6}"
            )
        if len(products) > 10:
            print(f"  … and {len(products) - 10} more rows in {OUTPUT_FILE}")
    else:
        log.warning("No products scraped. Amazon may have blocked the request.")