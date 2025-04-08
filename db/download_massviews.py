import os
import time
import glob
from tqdm import tqdm
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Ensure the download folder is ajacent to this script
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data\\massviews")
START_DATE = "2024-01-01"
END_DATE = "2025-01-01"

def setup_driver():
    """Configure Chrome driver with headless mode"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")
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

def is_file_downloaded(file_path, check_interval=0.25, max_checks=5):
    """Check if the file is fully downloaded by ensuring its size stabilizes."""
    previous_size = -1
    for _ in range(max_checks):
        current_size = os.path.getsize(file_path)
        if current_size == previous_size:
            return True  # File size has stabilized
        previous_size = current_size
        time.sleep(check_interval)
    return False

def wait_for_new_download(initial_file_count, timeout=60):
    """Wait for a new file to be downloaded and ensure it's fully downloaded."""
    start_time = time.time()

    while (time.time() - start_time) < timeout:
        # Get all JSON files in the download directory
        current_files = glob.glob(os.path.join(DOWNLOAD_DIR, '*.json'))
        current_file_count = len(current_files)

        # Check if a new file has been added
        if current_file_count > initial_file_count:
            # Find the most recently created file
            latest_file = max(current_files, key=os.path.getctime)

            # Ensure the file is not still being written to (size stabilizes)
            if is_file_downloaded(latest_file):
                return latest_file

        time.sleep(1)  # Wait before checking again

    raise TimeoutError("Download timed out. No new valid JSON file was found.")


def download_massviews(category):
    """
    Download MassViews data for a given Wikipedia category.
    
    :param category: The Wikipedia category to analyze (e.g., "Condensed matter physics").
    """
    driver = setup_driver()
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Navigate to the webpage
    url = f"https://pageviews.wmcloud.org/massviews/?platform=all-access&agent=user&source=category&start={START_DATE}&end={END_DATE}&subjectpage=1&subcategories=1&sort=views&direction=1&view=list&target=https://en.wikipedia.org/wiki/Category:{category.replace(' ', '_')}"
    driver.get(url)
    
    print(f"Starting massviews analysis scrape for \"{category}\"...")

    try:
        # Wait for page to fully load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.progress-counter"))
        )

        ## We attach to the website's progress counter to monitor progress and completion.
        # Initialize the progress bar
        progress_bar = None

        # Monitor the progress counter
        while True:
            try:
                # Find the progress counter element
                progress_element = driver.find_element(By.CSS_SELECTOR, "div.progress-counter")
                progress_text = progress_element.text.strip()

                # Extract the current and total progress using regex
                match = re.search(r"Processing page (\d+) of (\d+)", progress_text)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))

                    # Initialize the progress bar if not already done
                    if progress_bar is None:
                        progress_bar = tqdm(total=total, desc="Processing Pages", unit="page")

                    # Update the progress bar
                    progress_bar.n = current
                    progress_bar.refresh()

                # If data has already been processed (which creates the progress_bar) and the text is empty, then processing is complete.
                elif progress_text == "" and progress_bar is not None:
                    print("Processing complete.")
                    break
                # Print status
                else: 
                    print(progress_text, end="\r")
            except Exception as e:
                print(f"Error reading progress counter: {e}")
                break

            time.sleep(0.5)  # Poll every 0.5 seconds

        
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
        
        initial_file_count = len(glob.glob(os.path.join(DOWNLOAD_DIR, '*.json')))

        print("Downloading...")
        # Click JSON download
        json_btn = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.download-json"))
        )
        safe_click(driver, json_btn)

        downloaded_file = wait_for_new_download(initial_file_count)
        print(f"Downloaded: {os.path.basename(downloaded_file)}")
        new_filename = f'{category}.json'
        new_filepath = os.path.join(os.path.dirname(os.path.abspath(downloaded_file)), new_filename)
        os.replace(os.path.abspath(downloaded_file), new_filepath)
        print(f"Renamed to: {new_filename}")
        return new_filepath
        
    except TimeoutException as e:
        print(f"Timeout occurred for: {str(e)}")
    except Exception as e:
        print(f"Error processing: {str(e)}")
    finally:
      driver.quit()