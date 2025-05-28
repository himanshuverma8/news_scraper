# News Scraper

## Installation

### Prerequisites
- Python 3.8+
- Install dependencies by running:
  ```
  pip install -r utils/requirements.txt
  ```

## Usage

This project includes four main scripts, each serving a distinct purpose for scraping, storing, and serving news data.

### 1. RSS Scraper (`rss_scraper.py`)
Fetches and stores news articles from a list of RSS feeds into CSV and XLSX files.

**Prepare RSS Feed List:**
- Add RSS feed URLs to `utils/rss_feeds.txt`. Example:
  ```
  https://rss.nytimes.com/services/xml/rss/nyt/World.xml
  https://feeds.bbci.co.uk/news/world/rss.xml
  https://www.thehindu.com/news/national/feeder/default.rss
  ```

**Run the Script:**
```
python rss_scraper.py
```

**What it does:**
- Reads RSS feed URLs from `utils/rss_feeds.txt`.
- Fetches news articles using robust, retry-enabled HTTP requests.
- Parses and cleans article details (title, summary, link, date, image, author, etc.).
- Detects the country source based on the feed URL.
- Removes duplicates and sorts articles by data completeness (most complete entries at the top).
- Saves output to:
  - `rss_scraped_data/csv/rss_scraped_data_output.csv`
  - `rss_scraped_data/xlsx/rss_scraped_data_output.xlsx`

### 2. RSS Scraper with Database Save (`rss_scraper_db_save.py`)
Fetches news articles and stores them in a Supabase PostgreSQL database.

**Setup:**
- Create a `.env` file in the project root with:
  ```
  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_ANON_KEY=your_anon_or_service_role_key
  ```
- Load environment variables in your script:
  ```python
  from dotenv import load_dotenv
  load_dotenv()
  ```

**Run the Script:**
```
python rss_scraper_db_save.py
```

**What it does:**
- Reads RSS feed URLs from `utils/rss_feeds.txt`.
- Fetches and parses feeds using robust HTTP requests with retry logic.
- Extracts article details (title, link, date, author, image, summary, etc.).
- Cleans HTML content from summaries using BeautifulSoup4.
- Infers the country source from the feed URL.
- Adds a timestamp for when the article was scraped.
- Upserts news records into a Supabase table, using `guid` to avoid duplicates.

### 3. Historical Data Scraper (`historical_data.py`)
Fetches historical news data by month for each country using Google News RSS.

**Initialize TextBlob (First Time Only):**
- Download necessary corpora:
  ```
  python -m textblob.download_corpora
  ```

**Run the Script:**
```
python historical_data.py
```

**What it does:**
- Queries historical news by month for each country from Google News RSS.
- Parses article details (title, publication date, link, summary, author, source).
- Extracts publisher domain and computes a sentiment score for the summary using TextBlob.
- Stores country-wise news data in:
  - `historical_data/csv/`
  - `historical_data/xlsx/`
- Generates a summary including:
  - Country name
  - Top 10 unique news agencies
  - Total articles downloaded
  - Date range

### 4. FastAPI Server (`api.py`)
Serves scraped news data via a REST API.

**Setup:**
- Create a `.env` file in the project root with:
  ```
  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_ANON_KEY=your_anon_or_service_role_key
  ```
- Load environment variables in your script:
  ```python
  from dotenv import load_dotenv
  load_dotenv()
  ```

**Run the API Server:**
```
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**Endpoints:**
- `GET /api/news/{page}`: Retrieve paginated news (default: 100 articles per page).
- `GET /api/news/search`: Search and filter news with pagination.
- `GET /api/news/latest`: Get the latest news (default: 10 items).
- `GET /api/stats`: Get news database statistics.
- `GET /health`: Health check for database connectivity.
- `POST /api/update`: Triggers the `rss_scraper_db_save.py` script to refresh news data.

## Issues Encountered and Optimizations

- **CSV/XLSX Output Issues:**
  - Problem: Randomly arranged data with missing or undefined values in some fields.
  - Solution: Implemented checks for every parameter, used BeautifulSoup4's `clean_html()` to remove HTML from summaries, and added a custom sorting function to prioritize entries with the most valid fields. Undefined values were replaced with alternate text.
  
- **Historical Data Limitations:**
  - Problem: Standard RSS feeds only provide recent data, not historical data for a full year.
  - Solution: Utilized Google News RSS to fetch one year of country-specific data, ensuring no invalid fields or errors in summaries.

- **API Performance:**
  - Problem: High latency when fetching all news data at once.
  - Solution: Implemented pagination logic (e.g., `/api/news/1` fetches the first 100 articles, then the next 100, etc.) to reduce latency and improve performance.

## Bonus Features Implemented

- **Supabase PostgreSQL Integration**: Stores scraped news data in a Supabase PostgreSQL database for efficient querying and management.
- **FastAPI for Frontend**: Built a REST API using FastAPI to serve news data as JSON, enabling seamless integration with frontend applications.
- **Language Detection**: Detects the language of articles using the JSON `language` parameter.
- **Cron Job for Updates**: Implemented a cron job triggered by a `POST /api/update` request, which runs the `rss_scraper_db_save.py` script to refresh the news data in the database.
- **Hosted on Render**: Deployed the API on Render for live access to fresh news feed data. Access the latest news at: [https://news-scraper-ipfp.onrender.com/api/news/1](https://news-scraper-ipfp.onrender.com/api/news/1).
## 📸 Preview  

![api callback response](https://res.cloudinary.com/de5vcnanx/image/upload/v1748446438/Screenshot_2025-05-28_at_9.01.42_PM_yz4jxm.png) 
![api callback response](https://res.cloudinary.com/de5vcnanx/image/upload/v1748446438/Screenshot_2025-05-28_at_9.01.54_PM_clnrqj.png)  