News Scrapper
How to install dependencies:
run this command "pip install -r utils/requirements.txt"
How to run the script:
there are four scripts for the different use cases 
1.rss_scraper.py
Prepare RSS Feed List: in the utils/rss_feeds.txt
example:https://rss.nytimes.com/services/xml/rss/nyt/World.xml
https://feeds.bbci.co.uk/news/world/rss.xml
https://www.thehindu.com/news/national/feeder/default.rss
run this command "python rss_scraper.py"
This Python script automatically fetches, parses, and stores news articles from a list of global RSS feed URLs.

On running, it will:
Read a list of RSS feed URLs from utils/rss_feeds.txt

Fetch news articles from each feed using robust retry-enabled HTTP requests

Parse and clean article details (title, summary, link, date, image, author, etc.)

Detect the country source based on the feed URL

Remove duplicates and sort by data completeness

Save the final news data into:

rss_scraped_data/csv/rss_scraped_data_output.csv

rss_scraped_data/xlsx/rss_scraped_data_output.xlsx
2.rss_scraper_db_save.py
Create a .env file in your project root:
Copy
Edit
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_or_service_role_key
from dotenv import load_dotenv
load_dotenv()
run this command: "python rss_scraper_db_save.py"
On running the script, it:
Reads RSS feed URLs from utils/rss_feeds.txt

Fetches and parses each RSS feed using robust HTTP requests with retry logic

Extracts relevant article details like title, link, date, author, image, summary, etc.

Cleans up HTML content from summaries

Infers the country source from the feed URL

Adds a timestamp for when the article was scraped

Upserts all news records into your Supabase table, using guid to avoid duplicates or overwrites

3.historical_data.py
Initialize TextBlob (First Time Only)
Download necessary corpora:
run the following command: "python -m textblob.download_corpora"
run the following command: "python historical_data.py"
On running the script, it:
Queries historical news by month for each country from Google News RSS

Parses article title, publication date, link, summary, author, and source

Extracts publisher domain and computes a sentiment score for the summary

Stores country-wise news data in:

historical_data/csv/

historical_data/xlsx/

Generates a summary with:

Country name

Top 10 unique news agencies

Total articles downloaded

Date range

4.api.py
Create a .env file in your project root:
Copy
Edit
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_or_service_role_key
from dotenv import load_dotenv
load_dotenv()
Run the API server
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
GET /api/news/{page}: Retrieve paginated news (100 per page default).

GET /api/news/search: Search and filter news with pagination.

GET /api/news/latest: Get latest news (default 10 items).

GET /api/stats: Get news database statistics.

GET /health: Health check for database connectivity.

POST /update: Run the rss_scraper_db_save.py script to refresh news data.

Issues Encountered and optimizations:
while i was generating the csv and xlsx files for the scrapped data there was a issue that it was randomly arranged with some values missing and undefined for some parameters i handeled that issue by checking for every parameter and also some summary have html intact even after scrapping i fixed that using beautifulsoup4 clean_html() and i also used a custom sorting function before saving the data so that the data with most number of valid fields are at the top always and the values which are not defined i added an alternate text.
for genarating historical data i was facing the issue of getting the data for one year which was possible with rss of every site as it only provides recent data hence to fix this issue i use google rss feed to get one year data of the countries and to generate the summaries as it has not any invalid fields and errors
while creating the api for fetching the scraped news data from the database i faced the  issue of loading the whole data in one go which lead to very high latency and fetch time hence to optimize this i added a pagination logic so that for /api/news/1 fetches the first 100 news first and then next set of 100 and so on.
Bonus Features I Implemented:
storing the data in supabase PostgreSQL data base.
an api using fastapi to fetch all the news in form of json to serve the frontend if required
language detection using the json object language param
cron job this is implemented that whenver the user perfors a get request to /api/update the save to db script is executed the updated news feed is saved to the database.