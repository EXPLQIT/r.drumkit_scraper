import requests
from bs4 import BeautifulSoup
import os
import logging
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout
from requests.exceptions import HTTPError, ReadTimeout
from urllib3.util.retry import Retry
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
stop_requested = False 

base_url = 'https://old.reddit.com'
subreddit_path = '/r/drumkits/'
category = 'top'
time_filter = 'all'
download_directory = r'C:\TESTICLES'

if not os.path.exists(download_directory):
    os.makedirs(download_directory)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

session = requests.Session()
retry_strategy = Retry(
    total=2,
    status_forcelist=[500, 502, 503, 504],
    backoff_factor=0.3
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

def load_processed_urls(file_path):
    try:
        with open(file_path, 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

def save_processed_url(file_path, url):
    with open(file_path, 'a') as file:
        file.write(url + '\n')

def build_reddit_url(base_path, category, time_filter=None):
    url = f"{base_url}{base_path}{category}/"
    if category == 'top' and time_filter:
        url += f'?sort=top&t={time_filter}'
    return url

def get_soup(url):
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except (Timeout, RequestException, ReadTimeout) as e:
        logger.warning('Skipping URL %s due to timeout: %s', url, str(e))
        return None
    except HTTPError as http_err:
        logger.error('Failed to retrieve URL %s: %s', url, str(http_err))
        if http_err.response.status_code == 403:
            logger.warning('Skipping URL %s due to 403 Client Error (Forbidden)', url)
            return None
        return None

def download_file(url, filename):
    if not filename.endswith(('.zip', '.rar')):
        logger.info(f'Skipping {filename}: not a .zip or .rar file')
        return False
    try:
        response = session.get(url, stream=True, headers=headers, timeout=60)
        response.raise_for_status()
        content_length = int(response.headers.get('Content-Length', 0))
        if content_length < 10240:
            logger.warning('Skipped %s due to insufficient content length: %s', filename, content_length)
            return False

        full_path = os.path.join(download_directory, filename)
        if os.path.exists(full_path):
            logger.warning('%s already exists, skipping download', full_path)
            return False

        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info('Successfully downloaded %s', os.path.basename(full_path))
        return True
    except (RequestException, Exception) as e:
        logger.error('Failed to download %s: %s', url, str(e))
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

def scrape_and_download(url):
    if stop_requested:
        return
    soup = get_soup(url)
    if not soup:
        return

    processed_urls = set()
    # Enhanced filtering: check if link ends with .zip or .rar before adding
    links = (a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith(('.zip', '.rar')))
    for url in links:
        print("Processing URL:", url)  # Add this print statement
        file_id = extract_file_id(url)
        if file_id and url not in processed_urls:
            filename = f"{file_id}.{url.rsplit('.', 1)[1]}"  # Keeps the original file extension
            processed_urls.add(url)
            direct_download_url = url if not url.startswith('drive.google.com') else f'https://drive.google.com/uc?export=download&id={file_id}'
            download_file(direct_download_url, filename)

def main():
    url_log_path = os.path.join(download_directory, 'downloaded_urls.log')
    processed_urls = load_processed_urls(url_log_path)

    start_time = time.time()
    prompt_interval = 60  # 10 minutes in seconds
    last_prompt_time = start_time

    current_url = build_reddit_url(subreddit_path, category, time_filter)
    while current_url:
        if time.time() - last_prompt_time >= prompt_interval:
            response = input("Do you want to continue scraping? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("User opted to stop scraping.")
                break
            last_prompt_time = time.time()

        soup = get_soup(current_url)
        if soup:
            with ThreadPoolExecutor(max_workers=10) as executor:
                links = [a['href'] for a in soup.find_all('a', class_='title') if 'href' in a.attrs and a['href'] not in processed_urls]
                for link in links:
                    processed_urls.add(link)
                    save_processed_url(url_log_path, link)
                executor.map(scrape_and_download, links)
            next_button = soup.find('span', class_='next-button')
            current_url = next_button.find('a')['href'] if next_button else None
        else:
            break

    logger.info('Scraping complete in %.2f seconds.', time.time() - start_time)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error('An error occurred in the main loop: %s', str(e))