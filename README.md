
# ThingiScraper
A scraper for Thingiverse

This is no longer in development as Thingiverse has changed the way their site works and I don't have time to keep up with it.

## Usage

    usage: main.py [-h] [-o OUT_DIR] [-re] scrape_thing thing_id

    positional arguments:
      scrape_thing          Scrapes a Thingiverse things page. Grabs the Summary, Images, and Files
      thing_id              The number in the Thingiverse url ex. 1234567 is the thing_id of https://thingiverse.com/thing:1234567
    
    optional arguments:
      -h, --help            show this help message and exit
      -o OUT_DIR, --out_dir OUT_DIR
                            The directory to save all the scraped data. It will be named the same as the Thingiverse design's name
      -re, --redownload     If a folder already exists with the same thing name, download it again.

Example:

    python main.py scrape_thing 1234567 -o "C:\Users\Admin\Documents\" -re
