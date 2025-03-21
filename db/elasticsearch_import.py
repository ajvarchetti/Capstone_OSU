import time
import json
import requests
import os
from elasticsearch import Elasticsearch, helpers

# Configure Elasticsearch
ES_HOST = os.getenv("ES_HOST")
if not ES_HOST:
    raise EnvironmentError("The environment variable 'ES_HOST' is not set. Do you have a .env file?")

INDEX_NAME = "wikipedia_conspiracies"
WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
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

def preprocess_data(data):
    valid_data = []
    for item in data:
        try:
            # 允许用 title 作为 label
            label = item.get("label") or item.get("title")
            if not label or not isinstance(label, str):
                raise ValueError("Missing 'label' or incorrect format")

            topic = label.replace("_", " ")  # 转换 Wikipedia 页面格式
            response = requests.get(WIKI_API_URL + topic, timeout=10)

            if response.status_code == 200:
                wiki_data = response.json()
                content = wiki_data.get("extract", "No content available.")
                url = wiki_data.get("content_urls", {}).get("desktop", {}).get("page", "")
            else:
                content = "No content available."
                url = ""

            if content == "No content available.":
                # 保留这个警告但简化
                print(f"No Wikipedia content found for: {topic}")
                continue  # 跳过没有内容的项

            valid_data.append({
                "title": topic,
                "label": label,  # 确保 label 存在
                "wikipedia_content": content,
                "source_url": url
            })
            # 移除每个处理成功的打印

        except (ValueError, requests.exceptions.RequestException) as e:
            print(f"Skipping invalid data - {str(e)}")

    return valid_data

# Connect to Elasticsearch and import data
def import_data():
    es = Elasticsearch(ES_HOST)

    # Check if index exists
    if es.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' already exists")
    else:
        es.indices.create(index=INDEX_NAME)
        print(f"Index '{INDEX_NAME}' created successfully")

    # Read JSON data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON data: {e}")
        return

    # Preprocess data
    data = preprocess_data(data)

    if not data:
        print("No valid data to import")
        return

    # Bulk import data
    actions = [{"_index": INDEX_NAME, "_source": item} for item in data]

    try:
        helpers.bulk(es, actions)
        print(f"Successfully imported {len(data)} records into '{INDEX_NAME}' index")
    except helpers.BulkIndexError as e:
        print(f"Some data is invalid, total {len(e.errors)} errors")
        # 移除错误详情的打印

if __name__ == "__main__":
    print("Starting data import...")
    wait_for_es()  # Ensure Elasticsearch is running
    import_data()  # Import JSON data
