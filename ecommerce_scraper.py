"""
E-commerce Product Data Extractor
Scrapes product data from books.toscrape.com (public demo site - ethical scraping)
Skills demonstrated: BeautifulSoup, Requests, multi-page scraping,
data cleaning, validation, CSV + JSON export
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time

BASE_URL = "https://books.toscrape.com/catalogue/"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

def scrape_page(url):
    """Scrape a single page and return list of book dicts."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    books = []

    for article in soup.select("article.product_pod"):
        try:
            title = article.select_one("h3 a")["title"].strip()
            price_raw = article.select_one(".price_color").text.strip()
            price = float(price_raw.replace("Â", "").replace("£", "").strip())
            rating_word = article.select_one("p.star-rating")["class"][1]
            rating = RATING_MAP.get(rating_word, 0)
            availability = article.select_one(".availability").text.strip()

            books.append({
                "title": title,
                "price_gbp": price,
                "rating": rating,
                "availability": availability
            })
        except Exception as e:
            print(f"[WARNING] Skipped a record due to: {e}")
            continue

    return books


def get_next_page(soup):
    """Return next page URL or None if last page."""
    next_btn = soup.select_one("li.next a")
    if next_btn:
        return BASE_URL + next_btn["href"]
    return None


def validate(df):
    """Basic validation checks."""
    print("\n--- Validation Report ---")
    print(f"Total records: {len(df)}")
    print(f"Missing titles: {df['title'].isnull().sum()}")
    print(f"Missing prices: {df['price_gbp'].isnull().sum()}")
    print(f"Price range: £{df['price_gbp'].min()} – £{df['price_gbp'].max()}")
    print(f"Rating range: {df['rating'].min()} – {df['rating'].max()}")
    print("Validation passed." if df.isnull().sum().sum() == 0 else "WARNING: Nulls detected.")


def main(max_pages=5):
    all_books = []
    url = START_URL
    page = 1

    print(f"Starting scrape — up to {max_pages} pages...\n")

    while url and page <= max_pages:
        print(f"Scraping page {page}: {url}")
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        books = scrape_page(url)
        all_books.extend(books)

        url = get_next_page(soup)
        page += 1
        time.sleep(1)  # polite delay

    df = pd.DataFrame(all_books)

    # Normalize & clean
    df["title"] = df["title"].str.strip()
    df["availability"] = df["availability"].str.strip()
    df.drop_duplicates(inplace=True)

    validate(df)

    # Export
    df.to_csv("books_data.csv", index=False)
    df.to_json("books_data.json", orient="records", indent=2)
    print(f"\nExported {len(df)} records to books_data.csv and books_data.json")


if __name__ == "__main__":
    main(max_pages=5)
