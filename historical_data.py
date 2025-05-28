from datetime import datetime, timedelta
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus
from textblob import TextBlob
import time
import os

# Country-specific search queries
countries = {
    "india": "India",
    "china": "China",
    "usa": "United States",
    "singapore": "Singapore"
}

# Date range for 1 year
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=365)

# Split the date range into monthly chunks
def generate_date_ranges(start, end, delta=30):
    ranges = []
    while start < end:
        chunk_end = min(start + timedelta(days=delta), end)
        ranges.append((start, chunk_end))
        start = chunk_end
    return ranges

# Fetch articles for a given country
def fetch_articles_for_country(country_name, query):
    date_ranges = generate_date_ranges(start_date, end_date)
    all_articles = []

    for start, end in date_ranges:
        time.sleep(1)  # Avoid rate limiting
        print(f"🔍 Fetching: {query} after:{start.date()} before:{end.date()}")
        encoded_query = quote_plus(f"{query} after:{start.date()} before:{end.date()}")
        feed_url = (
            f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        )
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                summary = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text()
                sentiment = TextBlob(summary).sentiment.polarity
                all_articles.append({
                    "Title": entry.get("title", "N/A"),
                    "Link": entry.get("link", "N/A"),
                    "Published": entry.get("published", "N/A"),
                    "Summary": summary,
                    "Source": entry.get("source", {}).get("title", "Google News"),
                    "Author": entry.get("author", "N/A"),
                    "Publisher Domain": urlparse(entry.get("link", "")).netloc,
                    "Sentiment Score": round(sentiment, 3),
                    "Scraped Time": datetime.utcnow().isoformat()
                })
        except Exception as e:
            print(f"❌ Error fetching data for {country_name}: {e}")

    return all_articles

# Create output folders if not already present (optional safety)
os.makedirs("historical_data/csv", exist_ok=True)
os.makedirs("historical_data/xlsx", exist_ok=True)

# Prepare summary data container
summary_rows = []

# Process each country and save the results
for country_code, query in countries.items():
    print(f"\n📥 Processing country: {query}")
    articles = fetch_articles_for_country(country_code, query)
    df = pd.DataFrame(articles)

    csv_path = f"historical_data/csv/historical_data_{country_code}.csv"
    xlsx_path = f"historical_data/xlsx/historical_data_{country_code}.xlsx"

    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False)

    print(f"✅ Saved data for {query}:")
    print(f"   → {csv_path}")
    print(f"   → {xlsx_path}")
    print(f"   📊 Total articles: {len(df)}")

    # Prepare summary info
    if not df.empty:
        unique_sources = sorted(df['Source'].dropna().unique())
        agency_str = ", ".join(unique_sources[:10]) + ("..." if len(unique_sources) > 10 else "")
    else:
        agency_str = "N/A"

    summary_rows.append({
        "Country": query,
        "News Agency": agency_str,
        "Total Articles Downloaded": len(df),
        "Total Historical Data": "Since " + start_date.strftime("%Y")
    })

# Create summary DataFrame
summary_df = pd.DataFrame(summary_rows)

# Save summary CSV and XLSX
summary_csv_path = "historical_data/summary.csv"
summary_xlsx_path = "historical_data/summary.xlsx"

summary_df.to_csv(summary_csv_path, index=False)
summary_df.to_excel(summary_xlsx_path, index=False)

print("\n✅ Finished processing all countries.")
print(f"Summary saved to:\n → {summary_csv_path}\n → {summary_xlsx_path}")
