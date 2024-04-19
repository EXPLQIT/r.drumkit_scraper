<!-- GETTING STARTED -->
## r/Drumkits Scraper Tool

Basically scrapes the 'all' category in r/Drumkits for download links and downloads them to a specified folder. 

It'll prompt every 1 minute if you want to continue scraping, you can adjust how often the prompt asks here:
```sh
  prompt_interval = 60 # This is in seconds (1 minute is default)
  ```

You can install the required library using pip:
```sh
  pip install requests beautifulsoup4
  ```

Be sure to change this to the location you wish to have the downloads in:
```sh
  download_directory = r'YOUR\LOCATION\GOES\HERE'
  ```
# Notes:

- If you stop the script for whatever reason and run the script again, it wont download previously downloaded packs. A downloaded_urls.txt file will be created upon running the script for the first time, it'll log the links that'll already be downloaded so I wouldn't delete the download_urls.txt file unless you want it to re-download all the packs again.
- It wont download every link in the subreddit, it'll bypass links that are problematic for the most part.
- If it seems like it's getting hung up on something, give it a few minutes, it'll eventually start up again. If it doesn't do anything at all, stop the script and run it again. It'll skip previously downloaded files.
- I played with the time_filter, changing it to month, week, or day and it didn't seem to function properly (haven't quite figured that out yet).
- I haven't let it scrape for longer than about 20-30 minutes, so I'm not sure if it'll get hung up on something down the line.

*entirely made with ChatGPT*

## *Bonus Meme*

I've included a script to extract all the rars/zips to a specified folder as well and cleans up the folder names (sorta kinda). 
* You need 7-Zip for this to work. *

You will need to update the location of the 7-Zip executable (7z.exe) here:

```sh
  result = subprocess.run(['7ZIP\EXE\LOCACTION\GOES\HERE', 'x', file_path, f'-o{extraction_target_folder}'], check=True, text=True, capture_output=True)
  ```

Be sure to update the source path (where the rar files are located) and the destination_folder (where you want the exported zips/rars.)
You can update them here:
```sh
  source_folder = r'SOURCE\FOLDER\PATH\HERE'
  destination_folder = r'DEST\FOLDER\PATH\HERE'
  ```
