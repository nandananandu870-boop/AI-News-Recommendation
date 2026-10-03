import os
import requests
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv


# Load .env
load_dotenv()

# Configuration
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# News collection
news_collection = db["news"]

# Prevent duplicate articles using URL
news_collection.create_index("url", unique=True)

# GNews API endpoint
GNEWS_URL = "https://gnews.io/api/v4/top-headlines"


def fetch_news(
    category="technology",
    country="in",
    lang="en",
    max_articles=10
):
    """
    Fetch news from GNews and store it in MongoDB.
    """

    if not GNEWS_API_KEY:
        raise RuntimeError("GNEWS_API_KEY is missing in .env")

    # API key is sent securely in the request header
    headers = {
        "X-Api-Key": GNEWS_API_KEY
    }

    # Request parameters
    params = {
        "category": category,
        "country": country,
        "lang": lang,
        "max": max_articles
    }

    # Send request to GNews
    response = requests.get(
        GNEWS_URL,
        headers=headers,
        params=params,
        timeout=30
    )

    # Stop if API returns an error
    response.raise_for_status()

    # Convert response to JSON
    data = response.json()

    articles = data.get("articles", [])

    saved = 0
    duplicates = 0

    # Store each article in MongoDB
    for article in articles:

        news_document = {
            "title": article.get("title"),
            "description": article.get("description"),
            "content": article.get("content"),
            "url": article.get("url"),
            "image": article.get("image"),
            "publishedAt": article.get("publishedAt"),
            "source": article.get("source", {}),
            "category": category,
            "language": lang,
            "country": country,
            "fetchedAt": datetime.now(timezone.utc)
        }

        try:
            news_collection.insert_one(news_document)
            saved += 1

        except DuplicateKeyError:
            duplicates += 1

    return {
        "fetched": len(articles),
        "saved": saved,
        "duplicates": duplicates
    }
if __name__ == "__main__":

    categories = [
        "technology",
        "business",
        "sports",
        "science",
        "health",
        "entertainment"
    ]

    for category in categories:

        print(f"\nFetching {category} news...")

        try:
            result = fetch_news(
                category=category,
                country="in",
                lang="en",
                max_articles=10
            )

            print(result)

        except Exception as e:
            print(f"Error fetching {category} news:", e)