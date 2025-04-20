from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import requests
import os
import time

# Read the original data file
INPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/massviews")
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/articles")

# Wikipedia API endpoints
WIKI_SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_FULLTEXT_API = "https://en.wikipedia.org/w/api.php"

def fetch_wikipedia_content(title):
    """Fetch full Wikipedia page content and its URL"""
    title = title.replace(" ", "_")  # Convert spaces to underscores
    #print(f"🔍 Fetching Wikipedia data for: {title}")

    # Get the page URL
    summary_url = WIKI_SUMMARY_API + title
    page_url = ""
    try:
        response = requests.get(summary_url)
        if response.status_code == 200:
            wiki_data = response.json()
            page_url = wiki_data.get("content_urls", {}).get("desktop", {}).get("page", "")
        else:
            print(f"⚠️ Wikipedia Summary API failed for {title}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Wikipedia Summary API request failed: {e}")

    # Fetch full page content
    fulltext_params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": True,
        "titles": title
    }
    try:
        response = requests.get(WIKI_FULLTEXT_API, params=fulltext_params)
        if response.status_code == 200:
            wiki_data = response.json()
            pages = wiki_data.get("query", {}).get("pages", {})
            if pages:
                page_content = next(iter(pages.values())).get("extract", "No content available.")
                return page_content, page_url
        print(f"⚠️ Wikipedia Fulltext API failed for {title}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Wikipedia Fulltext API request failed: {e}")

    return "No content available.", page_url

def process_article(item, retries=5):
    """Process a single article and fetch Wikipedia content with retries."""
    # Handle both formats: "article" and "label"
    title = item.get("article") or item.get("label")
    daily_views = item.get("daily_views")
    
    if not title or not isinstance(title, str):
        #print(f"⚠️ Skipping invalid article: {item}")
        return None  # Skip invalid data

    title = title.replace("_", " ")  # Convert to Wikipedia page format

    for attempt in range(1, retries + 1):
        wikipedia_content, source_url = fetch_wikipedia_content(title)

        if wikipedia_content != "No content available.":
            # print(f"✅ Processed: {title}")
            return {
                "title": title,
                "wikipedia_content": wikipedia_content,
                "source_url": source_url,
                "daily_views": daily_views
            }
        else:
            print(f"⚠️ Attempt {attempt} failed for: {title}")
            if attempt < retries:
                time.sleep(6.0) # Wait before retrying (api seems to occasionally blackout for a few seconds)
                # print(f"🔄 Retrying for: {title}...")

    print(f"❌ All {retries} attempts failed for: {title}")
    return None  # Skip entries after exhausting retries

def download_articles_for_category(input_file_path):
    output_file_path = os.path.join(OUTPUT_FOLDER, os.path.basename(input_file_path))
    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"📂 Loaded {len(data)} entries from {os.path.basename(input_file_path)}")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"❌ Error: File {input_file_path} not found or not valid JSON!")
        return

    articles = []

    # Use ThreadPoolExecutor to parallelize the processing
    with ThreadPoolExecutor(max_workers=100) as executor:
        # Submit tasks for each article
        futures = {executor.submit(process_article, item): item for item in data}

        # Collect results as they complete
        for future in as_completed(futures):
            result = future.result()
            if result:
                articles.append(result)

    if articles:
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=4, ensure_ascii=False)
        print(f"\n🎉 Wiki Download complete! Data saved to {os.path.basename(output_file_path)}")
    else:
        print("❌ No valid data found, output file is empty!")

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    for filename in os.listdir(INPUT_FOLDER):
        if filename.endswith(".json"):
            input_file_path = os.path.join(INPUT_FOLDER, filename)
            download_articles_for_category(input_file_path)

if __name__ == "__main__":
    print("Starting data download...")
    main()
    
