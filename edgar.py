"""Utilities for looking up SEC Central Index Keys (CIKs)."""

import json
from html.parser import HTMLParser
from pathlib import Path
import time

import requests


CACHE_PATH = Path("cache/company_tickers.json")
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
USER_AGENT = "Elson ezenwachidiebere181@gmail.com"


class _TextExtractor(HTMLParser):
    """Collect visible text while ignoring HTML tags and embedded code."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self._ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data):
        if not self._ignored_depth:
            self.parts.append(data)


def _download_sec_json(url):
    """Download JSON from SEC after observing the request delay."""
    time.sleep(0.2)
    response = requests.get(url, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()


def _download_sec_text(url):
    """Download text from SEC after observing the request delay."""
    time.sleep(0.2)
    response = requests.get(url, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.text


def get_cik(ticker):
    """Return the zero-padded, 10-digit CIK for *ticker*."""
    if CACHE_PATH.exists():
        with CACHE_PATH.open(encoding="utf-8") as cache_file:
            companies = json.load(cache_file)
    else:
        companies = _download_sec_json(COMPANY_TICKERS_URL)

        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CACHE_PATH.open("w", encoding="utf-8") as cache_file:
            json.dump(companies, cache_file)

    ticker = ticker.upper()
    for company in companies.values():
        if company["ticker"].upper() == ticker:
            return str(company["cik_str"]).zfill(10)

    raise ValueError(f"Ticker not found: {ticker}")


def get_companyfacts(ticker):
    """Return SEC company facts JSON for *ticker*, using a local cache."""
    cik = get_cik(ticker)
    cache_path = Path("cache") / f"companyfacts_{ticker.upper()}.json"

    if cache_path.exists():
        with cache_path.open(encoding="utf-8") as cache_file:
            return json.load(cache_file)

    companyfacts = _download_sec_json(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as cache_file:
        json.dump(companyfacts, cache_file)

    return companyfacts


def get_10k_text(ticker):
    """Return the most recent 10-K as normalized plain text, using a cache."""
    cache_path = Path("cache") / f"10k_{ticker.upper()}.txt"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    cik = get_cik(ticker)
    submissions = _download_sec_json(
        f"https://data.sec.gov/submissions/CIK{cik}.json"
    )
    recent_filings = submissions["filings"]["recent"]
    for index, form in enumerate(recent_filings["form"]):
        if form == "10-K":
            accession_number = recent_filings["accessionNumber"][index]
            primary_document = recent_filings["primaryDocument"][index]
            break
    else:
        raise ValueError(f"No 10-K found for {ticker.upper()}")

    accession_no_dashes = accession_number.replace("-", "")
    document_url = (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession_no_dashes}/{primary_document}"
    )
    parser = _TextExtractor()
    parser.feed(_download_sec_text(document_url))
    text = " ".join(" ".join(parser.parts).split())

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(text, encoding="utf-8")
    return text


def extract_item(text, start_marker, end_marker):
    """Return text between headings, using the last start-marker occurrence."""
    lower_text = text.lower()
    start = lower_text.rfind(start_marker.lower())
    if start == -1:
        raise ValueError(f"Start marker not found: {start_marker}")

    end = lower_text.find(end_marker.lower(), start + len(start_marker))
    if end == -1:
        raise ValueError(f"End marker not found: {end_marker}")
    return text[start:end]


if __name__ == "__main__":
    item_7 = extract_item(get_10k_text("AAPL"), "Item 7.", "Item 7A.")
    print(len(item_7))
    print(item_7[:500])
