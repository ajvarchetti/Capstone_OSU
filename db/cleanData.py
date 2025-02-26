import json
import requests

# Read the original data file
input_file = "conspiracyData.json"
output_file = "cleaned_conspiracyData.json"

# Wikipedia API endpoint
WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

def fetch_wikipedia_content(title):
    """Fetch page content from Wikipedia API"""
    url = WIKI_API_URL + title.replace(" ", "_")  # Convert spaces to underscores
    try:
        response = requests.get(url)
        if response.status_code == 200:
            wiki_data = response.json()
            return wiki_data.get("extract", "No content available."), wiki_data.get("content_urls", {}).get("desktop", {}).get("page", "")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Wikipedia API request failed: {e}")
    return "No content available.", ""

def clean_data():
    """Clean conspiracyData.json and save it to cleaned_conspiracyData.json"""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File {input_file} not found!")
        return

    cleaned_data = []
    for item in data:
        if "label" not in item:
            continue  # Skip invalid data

        title = item["label"].replace("_", " ")  # Convert to Wikipedia page format
        wikipedia_content, source_url = fetch_wikipedia_content(title)

        cleaned_entry = {
            "title": title,
            "wikipedia_content": wikipedia_content,
            "source_url": source_url
        }
        cleaned_data.append(cleaned_entry)
        print(f"✅ Processed: {title}")

    # Save the cleaned data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    print(f"\n🎉 Cleaning complete! Data saved to {output_file}")

if __name__ == "__main__":
    clean_data()