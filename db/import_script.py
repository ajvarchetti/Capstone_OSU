import time
import json
import requests
from elasticsearch import Elasticsearch, helpers

# Configure Elasticsearch
ES_HOST = "http://localhost:9200"
INDEX_NAME = "wikipedia_conspiracies"
WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Wait for Elasticsearch to start
def wait_for_es():
    while True:
        try:
            response = requests.get(ES_HOST)
            if response.status_code == 200:
                print("✅ Elasticsearch is up and running!")
                break
        except requests.exceptions.ConnectionError:
            pass
        print("⏳ Waiting for Elasticsearch to start...")
        time.sleep(5)

# Preprocess data: Remove invalid entries & fetch Wikipedia content
def preprocess_data(data):
    valid_data = []
    for item in data:
        try:
            if "label" not in item or not isinstance(item["label"], str):
                raise ValueError("❌ Missing 'label' or incorrect format")

            topic = item["label"].replace("_", " ")  # Convert to Wikipedia page format
            response = requests.get(WIKI_API_URL + topic)

            if response.status_code == 200:
                wiki_data = response.json()
                content = wiki_data.get("extract", "No content available.")
                url = wiki_data.get("content_urls", {}).get("desktop", {}).get("page", "")
            else:
                content = "No content available."
                url = ""

            # Store only required fields
            valid_data.append({
                "title": topic,
                "wikipedia_content": content,
                "source_url": url
            })

        except ValueError as e:
            print(f"❌ Skipping invalid data {item} - {str(e)}")
    
    return valid_data

# Connect to Elasticsearch and import data
def import_data():
    es = Elasticsearch(ES_HOST)

    # Check if index exists
    if es.indices.exists(index=INDEX_NAME):
        print(f"😊 Index '{INDEX_NAME}' already exists, skipping creation")
    else:
        es.indices.create(index=INDEX_NAME)
        print(f"✅ Index '{INDEX_NAME}' created successfully!")

    # Read JSON data
    with open("conspiracyData.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Preprocess data
    data = preprocess_data(data)

    if not data:
        print("❌ No valid data to import")
        return

    # Bulk import data
    actions = [{"_index": INDEX_NAME, "_source": item} for item in data]

    try:
        helpers.bulk(es, actions)
        print(f"✅ Successfully imported {len(data)} records into '{INDEX_NAME}' index!")
    except helpers.BulkIndexError as e:
        print(f"❌ Some data is invalid, total {len(e.errors)} errors")
        for error in e.errors[:5]:  # Print only the first 5 errors
            print(error)

if __name__ == "__main__":
    wait_for_es()  # Ensure Elasticsearch is running
    import_data()  # Import JSON data
