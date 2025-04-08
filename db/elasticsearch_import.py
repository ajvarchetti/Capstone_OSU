import time
import json
import requests
import os
from elasticsearch import Elasticsearch, helpers

# Configure Elasticsearch
ES_HOST = os.getenv("ES_HOST")
if not ES_HOST:
    raise EnvironmentError("The environment variable 'ES_HOST' is not set. Do you have a .env file?")

INDEX_NAME = "wikipedia"
DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_FOLDER, "wiki_articles.json")
# Wait for Elasticsearch to start
def wait_for_es():
    while True:
        try:
            response = requests.get(ES_HOST, timeout=10)
            if response.status_code == 200:
                print("Elasticsearch is up and running")
                break
        except requests.exceptions.RequestException as e:
            print(f"Waiting for Elasticsearch to start... Error: {e}")
        time.sleep(5)

def create_index_with_mapping(es, index_name):
    mapping = {
        "mappings": {
            "properties": {
                "title": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "content": {
                    "type": "text",
                    "analyzer": "english"  # Use the English analyzer for better text analysis
                },
                "source_url": {
                    "type": "keyword"
                }
            }
        }
    }

    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=mapping)
        print(f"Index '{index_name}' created with custom mapping.")
    else:
        print(f"Index '{index_name}' already exists.")

# Connect to Elasticsearch and import data
def import_data():
    es = Elasticsearch(ES_HOST)
    create_index_with_mapping(es, INDEX_NAME)

    # Read JSON data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON data: {e}")
        return
    
    if not data:
        print("No valid data to import")
        return

    # Bulk import data
    articles = [
        {
            "_index": INDEX_NAME,
            "_id": item.get("title"),  # Use the "title" as the document ID to prevent duplicates
            "_source": item
        }
        for item in data
        if "title" in item  # Ensure "title" exists in the document
    ]

    try:
        helpers.bulk(es, articles)
        print(f"Successfully imported {len(articles)} records into '{INDEX_NAME}' index")
    except helpers.BulkIndexError as e:
        print(f"Some data is invalid, total {len(e.errors)} errors")

if __name__ == "__main__":
    print("Starting data import...")
    wait_for_es()  # Ensure Elasticsearch is running
    import_data()  # Import JSON data
