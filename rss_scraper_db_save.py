import feedparser
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from supabase import create_client, Client
import os

# -------------------------- SUPABASE CONFIG --------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLE_NAME = "news_feed"

# -------------------------- FEED URLS --------------------------
with open('utils/rss_feeds.txt') as f:
    rss_urls = [line.strip() for line in f if not line.startswith('#') and line.strip()]

# -------------------------- SETUP SESSION --------------------------
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[403, 404, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)
session.headers.update({
    'User-Agent': 'Mozilla/5.0'
})

news_data = []

# -------------------------- FUNCTIONS --------------------------
def fetch_news(url):
    try:
        print(f"🔍 Fetching from: {url}")
        response = session.get(url, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        for entry in feed.entries:
            summary_html = entry.get("summary", "")
            summary_text = clean_html(summary_html)

            news_data.append({
                "title": entry.get("title", "").strip() or None,
                "publication_date": entry.get("published", "").strip() or None,
                "source": feed.feed.get("title", "").strip() or None,
                "news_url": entry.get("link", "").strip() or None,
                "summary": summary_text or None,
                "country": get_country_from_url(url),
                "author": entry.get("author", "").strip() or None,
                "category": extract_category(entry).strip() or None,
                "guid": entry.get("id", entry.get("guid", "")).strip() or None,
                "image_url": extract_image_url(entry).strip() or None,
                "language": feed.feed.get("language", "").strip() or None,
                "scraped_timestamp": datetime.utcnow().isoformat()
            })

    except requests.exceptions.RequestException as req_err:
        print(f"❌ Network error with {url}: {req_err}")
    except Exception as e:
        print(f"❌ General error with {url}: {e}")

def get_country_from_url(url):
    url = url.lower()
    if 'cnn' in url or 'nytimes' in url: return 'USA'
    if 'bbc' in url: return 'UK'
    if 'cbc' in url: return 'Canada'
    if 'timesofindia' in url or 'thehindu' in url: return 'India'
    if 'abc.net.au' in url: return 'Australia'
    if 'dw.com' in url: return 'Germany'
    if 'france24' in url: return 'France'
    if 'nhk.or.jp' in url: return 'Japan'
    if 'xinhuanet' in url: return 'China'
    if 'straitstimes' in url: return 'Singapore'
    if 'thestar.com.my' in url: return 'Malaysia'
    if 'jakartapost' in url: return 'Indonesia'
    if 'koreatimes' in url: return 'South Korea'
    if 'rt.com' in url: return 'Russia'
    if 'globo.com' in url: return 'Brazil'
    if 'news24' in url: return 'South Africa'
    if 'gulfnews' in url: return 'UAE'
    if 'aljazeera' in url: return 'Qatar'
    if 'hurriyetdailynews' in url: return 'Turkey'
    if 'ansa.it' in url: return 'Italy'
    return 'Unknown'

def extract_category(entry):
    if "tags" in entry:
        return ", ".join([tag.get("term", "").strip() for tag in entry.tags if tag.get("term")])
    return ""

def extract_image_url(entry):
    if "media_thumbnail" in entry and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url", "")
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url", "")
    if "image" in entry:
        return entry.image.get("href", "")
    return ""

def clean_html(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def insert_to_supabase(data):
    for item in data:
        try:
            supabase.table(TABLE_NAME).upsert(item, on_conflict=["guid"]).execute()
        except Exception as e:
            print(f"❌ Failed to upsert record: {item['guid']}, Error: {e}")

# -------------------------- MAIN FLOW --------------------------
for url in rss_urls:
    fetch_news(url)

print(f"📥 Total news fetched: {len(news_data)}")
insert_to_supabase(news_data)
print("✅ Data inserted/updated to Supabase table successfully.")
