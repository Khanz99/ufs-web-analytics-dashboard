import json
import requests
from pathlib import Path

SERPAPI_KEY = "875e60725a26dd05eecba1edf82543a1cb8efe1e65fd6c8ce5f65c1afe7f7be4"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def fetch_google_trends(data_type):
    params = {
        "engine": "google_trends",
        "q": "/m/07vz0y", # This is the Google Trends topic ID for "South Africa"
        "geo": "ZA",
        "date": "now 7-d",
        "data_type": data_type,
        "api_key": SERPAPI_KEY
    }

    response = requests.get("https://serpapi.com/search.json", params=params)
    response.raise_for_status()
    return response.json()


def clean_top_items(items, limit=5):
    cleaned = []

    for item in items[:limit]:
        title = (
            item.get("topic", {}).get("title")
            or item.get("query")
            or item.get("title")
            or "Unknown"
        )

        item_type = (
            item.get("topic", {}).get("type")
            or item.get("type")
            or ""
        )

        value = (
            item.get("extracted_value")
            or item.get("value")
            or 0
        )

        cleaned.append({
            "title": title,
            "type": item_type,
            "value": value
        })

    return cleaned


print("Fetching Google Trends related topics...")
topics_data = fetch_google_trends("RELATED_TOPICS")

print("Fetching Google Trends related queries...")
queries_data = fetch_google_trends("RELATED_QUERIES")

topics_top = clean_top_items(
    topics_data.get("related_topics", {}).get("top", []),
    5
)

queries_top = clean_top_items(
    queries_data.get("related_queries", {}).get("top", []),
    5
)

topics = topics_top
queries = queries_top

final_data = {
    "related_topics": topics,
    "related_queries": queries
}

output_file = DATA_DIR / "google_trends.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=2, ensure_ascii=False)

print("Google Trends JSON updated successfully.")
print(f"Written to: {output_file}")
print(f"Topics: {len(topics_top)}")
print(f"Queries: {len(queries_top)}")