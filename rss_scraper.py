import feedparser
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

# Load RSS feed URLs
with open('utils/rss_feeds.txt') as f:
    rss_urls = [line.strip() for line in f if not line.startswith('#') and line.strip()]

news_data = []

# Setup a requests session with retry and headers
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[403, 404, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
})

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
                "Title": entry.get("title", "").strip() or "Title Not Found",
                "Publication Date": entry.get("published", "").strip() or "Publication Date Not Found",
                "Source": feed.feed.get("title", "").strip() or "Source Not Found",
                "News URL": entry.get("link", "").strip() or "URL Not Found",
                "Summary": summary_text or "Summary Not Found",
                "Country": get_country_from_url(url),
                "Author": entry.get("author", "").strip() or "Author Not Found",
                "Category": extract_category(entry).strip() or "Category Not Found",
                "GUID": entry.get("id", entry.get("guid", "")).strip() or "GUID Not Found",
                "Image URL": extract_image_url(entry).strip() or "Image URL Not Found",
                "Language": feed.feed.get("language", "").strip() or "Language Not Found",
                "Scraped Timestamp": datetime.utcnow().isoformat()
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
        terms = [tag.get("term", "").strip() for tag in entry.tags if tag.get("term", "").strip()]
        return ", ".join(terms) if terms else ""
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

# Fetch all feeds
for url in rss_urls:
    fetch_news(url)

# Create DataFrame
df = pd.DataFrame(news_data)
df.drop_duplicates(subset=["News URL"], inplace=True)

# Completeness check
required_fields = ["Title", "Publication Date", "Source", "News URL", "Summary", "Country"]
def compute_completeness(row):
    return sum(bool(row[field]) and row[field] not in [f"{field} Not Found" for field in required_fields] for field in required_fields)
df["Completeness"] = df.apply(compute_completeness, axis=1)
df.sort_values(by="Completeness", ascending=False, inplace=True)
df.drop(columns=["Completeness"], inplace=True)

# Save output
os.makedirs("rss_scraped_data/csv", exist_ok=True)
os.makedirs("rss_scraped_data/xlsx", exist_ok=True)

df.to_csv("rss_scraped_data/csv/rss_scraped_data_output.csv", index=False, encoding='utf-8')
df.to_excel("rss_scraped_data/xlsx/rss_scraped_data_output.xlsx", index=False, engine='openpyxl')

print("✅ News saved to rss_scraped_data/csv/rss_scraped_data_output.csv and rss_scraped_data/xlsx/rss_scraped_data_output.xlsx")
