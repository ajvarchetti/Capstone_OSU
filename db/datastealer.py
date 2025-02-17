import os
import json
import time
import glob
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Configuration
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'wikipedia_topviews_downloads')
COMBINED_FILE = 'wikipedia_topviews_combined.json'
START_DATE = "2015-07-01"
END_DATE = "2016-07-01"

def setup_driver():
    """Configure Chrome driver with headless mode"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    return webdriver.Chrome(options=chrome_options)

def daterange(start_date, end_date):
    """Generate dates between start and end dates"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    for n in range(int((end - start).days) + 1):
        yield start + timedelta(n)

def safe_click(driver, element):
    """Reliable element clicking with multiple fallbacks"""
    try:
        # Scroll to element with offset to account for header
        driver.execute_script("window.scrollTo(0, arguments[0].offsetTop - 100)", element)
        
        # Wait for element to be clickable
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable(element))
        
        # Try regular click
        element.click()
    except:
        # Fallback to JavaScript click
        driver.execute_script("arguments[0].click();", element)

def wait_for_download_complete(timeout=60):
    """Wait for latest download to complete"""
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        files = glob.glob(os.path.join(DOWNLOAD_DIR, '*.json'))
        if files and max(files, key=os.path.getctime).endswith('.json'):
            return max(files, key=os.path.getctime)
        time.sleep(1)
    raise TimeoutError("Download timed out")

def process_downloaded_file(file_path):
    """Process JSON file and extract articles"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        articles = []
        if isinstance(data, dict):
            articles = data.get('articles', data.get('items', []))
        elif isinstance(data, list):
            articles = data
            
        return articles
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return []

def merge_articles(all_articles):
    """Merge and deduplicate articles across all dates"""
    merged = {}
    for article in all_articles:
        name = article.get('article')
        if not name:
            continue
            
        views = int(article.get('views', article.get('count', 0)))
        
        if name in merged:
            merged[name]['views'] += views
        else:
            merged[name] = {
                'article': name,
                'views': views
            }
    
    sorted_articles = sorted(merged.values(), key=lambda x: x['views'], reverse=True)
    return sorted_articles

def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    driver = setup_driver()
    all_articles = []
    
    try:
        for single_date in daterange(START_DATE, END_DATE):
            current_date = single_date.strftime("%Y-%m-%d")
            print(f"\nProcessing date: {current_date}")
            
            url = f"https://pageviews.wmcloud.org/topviews/?project=en.wikipedia.org&platform=all-access&date={current_date}&excludes="
            driver.get(url)
            
            try:
                # Wait for page to fully load
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.download-btn-group"))
                )

                # Dismiss any overlays
                try:
                    driver.execute_script("""
                        var elements = document.querySelectorAll('div.data-notice');
                        elements.forEach(element => element.style.display = 'none');
                    """)
                except:
                    pass

                # Open download dropdown
                download_btn = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.download-btn-group button"))
                )
                safe_click(driver, download_btn)

                # Click JSON download
                json_btn = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.download-json"))
                )
                safe_click(driver, json_btn)

                # Wait for download
                downloaded_file = wait_for_download_complete()
                print(f"Downloaded: {os.path.basename(downloaded_file)}")
                
                # Process and collect articles
                articles = process_downloaded_file(downloaded_file)
                all_articles.extend(articles)
                
                # Clean up downloaded file
                os.remove(downloaded_file)
                
            except TimeoutException as e:
                print(f"Timeout occurred for {current_date}: {str(e)}")
                continue
            except Exception as e:
                print(f"Error processing {current_date}: {str(e)}")
                continue
                
        # Merge and save final results
        merged_articles = merge_articles(all_articles)
        print(f"\nTotal unique articles: {len(merged_articles)}")
        
        with open(COMBINED_FILE, 'w', encoding='utf-8') as f:
            json.dump(merged_articles, f, indent=2, ensure_ascii=False)
            
        print(f"\nSaved combined results to: {COMBINED_FILE}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()