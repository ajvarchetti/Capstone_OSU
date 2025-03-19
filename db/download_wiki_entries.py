import json
import requests

# Read the original data file
input_file = "conspiracy.json"
output_file = "cleaned_Conspiracy.json"

# Wikipedia API endpoints
WIKI_SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_FULLTEXT_API = "https://en.wikipedia.org/w/api.php"

def fetch_wikipedia_content(title):
    """Fetch full Wikipedia page content and its URL"""
    title = title.replace(" ", "_")  # Convert spaces to underscores
    print(f"🔍 Fetching Wikipedia data for: {title}")

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

def clean_data():
    """Clean data from topviews-2024.json and save it to cleaned_2024Data.json"""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"📂 Loaded {len(data)} entries from {input_file}")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"❌ Error: File {input_file} not found or not valid JSON!")
        return

    cleaned_data = []
    for item in data:
        # Handle both formats: "article" and "label"
        title = item.get("article") or item.get("label")

        if not title or not isinstance(title, str):
            print(f"⚠️ Skipping invalid entry: {item}")
            continue  # Skip invalid data

        title = title.replace("_", " ")  # Convert to Wikipedia page format

        wikipedia_content, source_url = fetch_wikipedia_content(title)

        if wikipedia_content == "No content available.":
            print(f"⚠️ No Wikipedia content found for: {title}")
            continue  # Skip entries with no Wikipedia data

        cleaned_entry = {
            "title": title,
            "wikipedia_content": wikipedia_content,
            "source_url": source_url
        }
        cleaned_data.append(cleaned_entry)
        print(f"✅ Processed: {title}")

    if cleaned_data:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
        print(f"\n🎉 Cleaning complete! Data saved to {output_file}")
    else:
        print("❌ No valid data found, output file is empty!")

if __name__ == "__main__":
    clean_data()
    
