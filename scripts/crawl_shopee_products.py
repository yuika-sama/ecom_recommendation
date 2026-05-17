"""
Crawler Shopee bang Selenium (giu theo repo mau, co them config).
Chay: python scripts/crawl_shopee_products.py --keywords-file samples/product-recommendation-system/crawler/shopee_crawler/products-keywords.txt
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from time import sleep

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver(user_data_dir: str | None, profile_directory: str | None, headless: bool) -> webdriver.Chrome:
    chrome_options = Options()
    if user_data_dir:
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    if profile_directory:
        chrome_options.add_argument(f"--profile-directory={profile_directory}")
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--start-maximized")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )


def sanitize_filename(name: str) -> str:
    return re.sub(r"[\\/*?:\"<>|]", "", name.replace(" ", "_"))


def _get_text(tag) -> str:
    return tag.text.strip() if tag else ""


def _get_attr(tag, attr: str) -> str:
    if tag and tag.has_attr(attr):
        return tag[attr]
    return ""


def scroll_page(driver: webdriver.Chrome, step: int = 800, max_scroll: int = 4000, pause: float = 2.0):
    height = 0
    while True:
        driver.execute_script(f"window.scrollTo({height}, {height + step});")
        sleep(pause)
        height += step
        if height >= max_scroll:
            break


def require_manual_login(driver: webdriver.Chrome, login_url: str = "https://shopee.vn/buyer/login"):
    driver.get(login_url)
    print("👉 Vui long dang nhap Shopee tren trinh duyet Selenium.")
    print("👉 Sau khi dang nhap xong, quay lai terminal va nhan Enter de tiep tuc...")
    input()


def parse_products(page_source: str) -> list[dict]:
    soup = BeautifulSoup(page_source, "html.parser")
    parents = soup.find_all("ul", class_="row shopee-search-item-result__items")
    if not parents:
        return []

    products = parents[0].find_all(
        "li", class_="col-xs-2-4 shopee-search-item-result__item"
    )
    results: list[dict] = []

    for product in products:
        name_tag = product.find(
            "div", class_="line-clamp-2 break-words min-w-0 min-h-[2.5rem] text-sm"
        )
        price_tag = product.find("span", class_="font-medium text-base/5 truncate")
        solds_tag = product.find(
            "div", class_="truncate text-shopee-black87 text-xs min-h-4"
        )
        img_tag = product.find(
            "img",
            class_="inset-y-0 w-full h-full pointer-events-none object-contain absolute",
        )
        rating_tag = product.find(
            "div", class_="text-shopee-black87 text-xs/sp14 flex-none"
        )
        location_tag = product.find(
            "div",
            class_="flex-shrink min-w-0 truncate text-shopee-black54 font-extralight text-sp10",
        )

        name = _get_text(name_tag)
        price = _get_text(price_tag)
        solds = _get_text(solds_tag)
        image = _get_attr(img_tag, "src")
        rating = _get_text(rating_tag)
        location = _get_text(location_tag)

        if name and price:
            results.append(
                {
                    "name": name,
                    "price": price,
                    "solds": solds,
                    "image": image,
                    "rating": rating,
                    "location": location,
                }
            )
    return results


def crawl_keyword(
    driver: webdriver.Chrome,
    keyword: str,
    output_dir: Path,
    max_pages: int,
    scroll_pause: float,
):
    url = f"https://shopee.vn/search?keyword={keyword}"
    print(f"🔎 {url}")
    driver.get(url)
    sleep(5)

    all_products: list[dict] = []
    page_count = 0

    while True:
        sleep(2)
        scroll_page(driver, pause=scroll_pause)
        all_products.extend(parse_products(driver.page_source))
        page_count += 1
        print(f"  Page {page_count}: total {len(all_products)} items")

        if max_pages and page_count >= max_pages:
            break

        try:
            nav = driver.find_elements(
                "css selector", "a.shopee-icon-button.shopee-icon-button--right"
            )
            if nav:
                aria_disabled = nav[0].get_attribute("aria-disabled")
                if aria_disabled == "true":
                    break
                nav[0].click()
            else:
                break
        except Exception as exc:
            print(f"⚠️ Khong the click Next: {exc}")
            break

    if not all_products:
        print(f"⚠️ Khong tim thay san pham cho keyword: {keyword}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"shopee_products_{sanitize_filename(keyword)}.csv"
    df = pd.DataFrame(all_products).drop_duplicates(subset=["name", "price", "image"])
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ Da luu {output_path} ({len(df)} san pham)")


def load_keywords(keywords_file: Path | None, keyword: str | None) -> list[str]:
    if keyword:
        return [keyword]
    if not keywords_file or not keywords_file.exists():
        return []
    return [line.strip() for line in keywords_file.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description="Shopee crawler (Selenium)")
    parser.add_argument("--keywords-file", type=str, default=None, help="Duong dan file keyword")
    parser.add_argument("--keyword", type=str, default=None, help="Mot keyword duy nhat")
    parser.add_argument("--output-dir", type=str, default="datas/recommend_dataset/prs_raw")
    parser.add_argument("--user-data-dir", type=str, default=None)
    parser.add_argument("--profile-directory", type=str, default=None)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--max-pages", type=int, default=0)
    parser.add_argument("--scroll-pause", type=float, default=2.0)

    args = parser.parse_args()
    if args.headless:
        print("⚠️ Khong the dang nhap thu cong o che do headless. Hay bo --headless.")
        return
    keywords_file = Path(args.keywords_file) if args.keywords_file else None
    keywords = load_keywords(keywords_file, args.keyword)
    if not keywords:
        print("⚠️ Khong co keyword nao duoc cung cap")
        return

    driver = setup_driver(args.user_data_dir, args.profile_directory, args.headless)
    try:
        require_manual_login(driver)
        for keyword in keywords:
            crawl_keyword(
                driver,
                keyword,
                output_dir=Path(args.output_dir),
                max_pages=args.max_pages,
                scroll_pause=args.scroll_pause,
            )
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
