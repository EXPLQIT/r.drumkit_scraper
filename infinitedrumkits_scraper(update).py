import requests
from bs4 import BeautifulSoup
import os
import logging
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout, HTTPError
from urllib3.util.retry import Retry
import time
import re
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Hardcoded parameters
base_url = 'https://old.reddit.com'
subreddit_path = '/r/drumkits/'  # Hardcoded subreddit path
download_directory = 'C:\\TESTICLES'  # Hardcoded download path

if not os.path.exists(download_directory):
    os.makedirs(download_directory)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

session = requests.Session()
retry_strategy = Retry(
    total=3,
    status_forcelist=[500, 502, 503, 504],
    backoff_factor=1
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

processed_urls = set()  # This should be initialized outside of the function
processed_urls_log_path = os.path.join(download_directory, 'processed_urls.log')

def load_processed_urls():
    try:
        with open(processed_urls_log_path, 'r') as file:
            return set(line.strip() for line in file)
    except FileNotFoundError:
        return set()

def save_processed_url(url):
    with open(processed_urls_log_path, 'a') as file:
        file.write(url + '\n')

def get_soup(url):
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        logger.error('Failed to retrieve URL %s due to error: %s', url, str(e))
        return None

def download_file(url, filename):
    try:
        response = session.get(url, stream=True, headers=headers, timeout=60)
        response.raise_for_status()
        full_path = os.path.join(download_directory, filename)
        if os.path.exists(full_path):
            logger.info('%s already exists. Skipping download.', full_path)
            return False
        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        logger.info('Successfully downloaded %s', filename)
        return True
    except Exception as e:
        logger.error('Failed to download %s due to error: %s', filename, str(e))
        return False
    
def extract_file_id(url):
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc
    if 'drive.google.com' in netloc and '/file/d/' in parsed_url.path:
        # Remove any query parameters (?usp=drivesdk, etc.)
        file_id = parsed_url.path.split('/file/d/')[1].split('/')[0]
        return file_id
    if 'mediafire.com' in netloc:
        return parsed_url.path.split('/')[-1]
    if 'dropbox.com' in netloc and '/s/' in parsed_url.path:
        return parsed_url.path.split('/s/')[1].split('/')[0]
    return None

def is_google_drive_link(url):
    return 'drive.google.com' in url

def get_google_drive_direct_link(file_id):
    # Google Drive direct link format for file downloads
    return f'https://drive.google.com/uc?export=download&id={file_id}'

def is_mediafire_link(url):
    return 'mediafire.com' in url

def get_mediafire_download_link(url):
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    download_button = soup.find('a', {'aria-label': 'Download file'})
    if download_button:
        return download_button['href']
    return None

def is_dropbox_link(url):
    return 'dropbox.com' in url

def get_dropbox_direct_link(url):
    if url.endswith('?dl=0'):
        return url.replace('?dl=0', '?dl=1')
    return url

def scrape_and_download(url):
    global processed_urls
    soup = get_soup(url)
    if not soup:
        return

    posts = soup.find_all('div', class_='thing', attrs={'data-domain': True})

    for post in posts:
        title = post.find('a', class_='title').get_text()
        link = post.find('a', class_='title')['href']

        if link in processed_urls:
            logger.info(f"Already processed {link}, skipping.")
            continue

        filename = sanitize_filename(title) + '.zip'  # Assume it's a zip file for simplicity
        direct_download_url = None  # Initialize as None

        if is_google_drive_link(link):
            print(f"Processing Google Drive link: {link}")
            file_id = extract_file_id(link)
            if file_id:
                direct_download_url = get_google_drive_direct_link(file_id)
                
        elif is_mediafire_link(link):
            print(f"Processing Mediafire link: {link}")
            direct_download_url = get_mediafire_download_link(link)
            
        elif is_dropbox_link(link):
            print(f"Processing Dropbox link: {link}")
            direct_download_url = get_dropbox_direct_link(link)

        # Check if a direct download URL was found, and proceed with downloading
        if direct_download_url and download_file(direct_download_url, filename):
            save_processed_url(link)

def sanitize_filename(filename):
    # Remove invalid file characters from the title
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def should_continue_scraping(start_time, interval=300):
    """Check if the time interval has passed and ask user whether to continue scraping."""
    if time.time() - start_time >= interval:
        response = input("Do you want to continue scraping? (yes/no): ").strip().lower()
        if response == "yes":
            return True, time.time()  # Reset the start time
        else:
            return False, time.time()
    return True, start_time

def main():
    global processed_urls
    processed_urls = load_processed_urls()
    print("Starting the scraper...")
    category = input("Enter the category (hot, new, rising, controversial, top, gilded): ")
    time_filter = ''
    if category == 'top':
        time_filter = input("Enter the time filter (hour, day, week, month, year, all): ")
        start_url = f"{base_url}{subreddit_path}{category}/?sort=top&t={time_filter}"
    else:
        start_url = f"{base_url}{subreddit_path}{category}/"

    print(f"Constructed URL: {start_url}")
    current_url = start_url
    start_time = time.time()  # Initialize the start time
    continue_scraping = True

    while current_url and continue_scraping:
        try:
            scrape_and_download(current_url)
            # Check if it's time to ask the user whether to continue
            continue_scraping, start_time = should_continue_scraping(start_time)
            # Find the 'next' button's link to the next page and update current_url
            soup = get_soup(current_url)
            next_button = soup.find('span', class_='next-button')
            current_url = next_button.find('a')['href'] if next_button and continue_scraping else None
        except Exception as e:
            print(f"An error occurred: {e}")
            logger.error(f"An error occurred: {e}")
            break  # Exit if an error occurs

    print("Scraping complete.")

if __name__ == "__main__":
    main()