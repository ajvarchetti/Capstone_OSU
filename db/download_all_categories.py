from download_massviews import download_massviews
import json
import os

DAILY_VIEW_THRESHOLD = 300
CATEGORIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "categories.json")

def process_massviews(filepath):
    # Load the JSON file
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
            print("JSON data loaded successfully!")
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

    # Filter and transform the data
    thresheld_data = []
    for item in data:
        average = item.get("average", 0)
        label = item.get("label", "No Label")
        if average > DAILY_VIEW_THRESHOLD:
            thresheld_data.append({
                "article": label,
                "daily_views": round(average)
            })

    try:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(thresheld_data, file, indent=4)
            print(f"Threshed data saved to {filepath}")
    except Exception as e:
        print(f"Error saving threshed data: {e}")

if __name__ == "__main__":
    # Load categories from JSON file
    try:
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as file:
            categories = json.load(file)
    except FileNotFoundError:
        print("Error: categories.json file not found.")
        categories = []
    except json.JSONDecodeError as e:
        print(f"Error decoding categories.json: {e}")
        categories = []

    # Download, process, and import each category
    for category in categories:
        massviews_file = download_massviews(category=category)
        if massviews_file:
            process_massviews(massviews_file)

    print("Massviews category data downloads complete")