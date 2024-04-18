<!-- GETTING STARTED -->
## r/Drumkits Scraper Tool

Basically scrapes the 'all' category for r/Drumkits and downloads them to a specified folder. 

It'll prompt every 10 minutes if you want to continue scraping, you can adjust how often the prompt asks here:
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

- It wont download every link in the subreddit, it'll bypass links that are problematic for the most part.
- If it seems like it's getting hung up on something, give it a few minutes, it'll eventually start up again.
- I played with the time_filter, changing it to month, week, or day and it didn't seem to function properly (haven't quite figured that out yet).
- I haven't let it scrape for longer than about 20-30 minutes, so I'm not sure if it'll get hung up on something down the line.

*entirely made with ChatGPT*
