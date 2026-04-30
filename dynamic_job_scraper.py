"""
Dynamic Job Listings Scraper
Scrapes job listings from quotes.toscrape.com/scroll (public JS-rendered demo)
Skills demonstrated: Selenium, infinite scroll, dynamic content,
hierarchical extraction, validation, CSV + JSON export
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import json
import time

URL = "https://quotes.toscrape.com/scroll"


def init_driver():
    """Initialize headless Chrome driver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


def scroll_and_collect(driver, max_scrolls=5):
    """Scroll page to trigger dynamic loading, collect all content."""
    driver.get(URL)
    time.sleep(2)

    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0

    while scrolls < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            print("Reached end of page.")
            break

        last_height = new_height
        scrolls += 1
        print(f"Scroll {scrolls} complete. Height: {new_height}px")

    return driver.page_source


def parse_content(html):
    """Parse loaded HTML and extract structured data."""
    soup = BeautifulSoup(html, "lxml")
    records = []

    for quote in soup.select("div.quote"):
        try:
            text = quote.select_one("span.text").text.strip().strip('\u201c\u201d')
            author = quote.select_one("small.author").text.strip()
            tags = [tag.text.strip() for tag in quote.select("a.tag")]

            records.append({
                "quote": text,
                "author": author,
                "tags": ", ".join(tags),
                "tag_count": len(tags)
            })
        except Exception as e:
            print(f"[WARNING] Skipped record: {e}")
            continue

    return records


def validate(df):
    """Consistency and quality checks."""
    print("\n--- Validation Report ---")
    print(f"Total records scraped: {len(df)}")
    print(f"Unique authors: {df['author'].nunique()}")
    print(f"Missing quotes: {df['quote'].isnull().sum()}")
    print(f"Missing authors: {df['author'].isnull().sum()}")
    print("All checks passed." if df.isnull().sum().sum() == 0 else "WARNING: Nulls found.")


def main():
    print("Launching browser...")
    driver = init_driver()

    try:
        html = scroll_and_collect(driver, max_scrolls=5)
    finally:
        driver.quit()

    records = parse_content(html)
    df = pd.DataFrame(records)
    df.drop_duplicates(subset=["quote"], inplace=True)

    validate(df)

    df.to_csv("quotes_data.csv", index=False)
    df.to_json("quotes_data.json", orient="records", indent=2)
    print(f"\nExported {len(df)} records to quotes_data.csv and quotes_data.json")


if __name__ == "__main__":
    main()
