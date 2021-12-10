import argparse
import os.path

import scraper

parser = argparse.ArgumentParser()
parser.add_argument("scrape_thing", help="Scrapes a Thingiverse things page. Grabs the Summary, Images, and Files",
                    type=str)
parser.add_argument("thing_id", help="The number in the Thingiverse url\n"
                                     "  ex. 1234567 is the thing_id of https://thingiverse.com/thing:1234567")
parser.add_argument("-o", "--out_dir", help="The directory to save all the scraped data.\n"
                                            "It will be named the same as the Thingiverse design's name",
                    type=str)
parser.add_argument("-re", "--redownload", help="If a folder already exists with the same thing name, download it again.",
                    action="store_true")
args = parser.parse_args()

out = None
if args.out_dir is None:
    out = scraper.get_script_dir()
elif os.path.exists(args.out_dir):
    out = args.out_dir
else:
    raise ValueError(f"Output directory doesn't exist:\n{args.out}")

print("Scraping...")

browser = scraper.get_driver(headless=True)
try:
    scraper.scrape_thing(browser, args.thing_id, output_dir=out, redownload=args.redownload)
except Exception as e:  # NOT good practice! But needs to catch crashes to close browser properly.
    #  Otherwise, there is memory leaks
    print("An error occurred:")
    print(e)
    print("Attempting to close browser properly...")
    browser.quit()
    print("Closed. Please try running again")
    raise e


