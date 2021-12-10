import os
import re
import requests
import time
from bs4 import BeautifulSoup
from pathlib import Path
from shutil import rmtree, copytree, ignore_patterns
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException


# def create_profile():
#     profile_path = str(Path(get_script_dir(), 'selenium_profile'))
#     if os.path.exists(profile_path):
#         print(f"Selenium profile found: {profile_path}")
#         return
#
#     print(f"Preparing a browser profile. This can take a minute...")
#     options = Options()
#     options.headless = True
#     service = Service(str(Path(get_script_dir(), "geckodriver.exe")))
#     try:
#         driver = Firefox(service=service, options=options)
#     except WebDriverException:
#         print("ERROR!\nPlease make sure 'geckodriver.exe' is located in the same directory as this script:\n"
#               f"{get_script_dir()}\n"
#               f"You can download it here: https://github.com/mozilla/geckodriver/releases")
#         return -1
#
#     print("Headless browser opened.")
#     driver.get('about:support')
#     time.sleep(2)  # Allow information to populate on page
#     temp_profile_dir = str(driver.find_element(By.ID, "profile-dir-box").text)
#
#     print("Creating selenium_profile... ", end="")
#     copytree(temp_profile_dir, str(Path(get_script_dir(), 'selenium_profile')), ignore=ignore_patterns('*.lock'))
#     driver.quit()
#     print("[OK]")


def get_driver(headless=True):
    # create_profile()
    options = Options()
    # options.add_argument("-profile")
    # options.add_argument(str(Path(get_script_dir(), 'selenium_profile')))
    options.headless = headless
    service = Service(str(Path(get_script_dir(), "geckodriver.exe")))
    try:
        driver = Firefox(service=service, options=options)
    except WebDriverException:
        print("ERROR!\nPlease make sure 'geckodriver.exe' is located in the same directory as this script:\n"
              f"{get_script_dir()}\n"
              f"You can download it here: https://github.com/mozilla/geckodriver/releases")
        return -1

    return driver


def get_script_dir():
    return str(os.path.dirname(os.path.abspath(__file__)))


def create_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def del_folder_contents(p):
    for path in Path(p).glob("**/*"):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            rmtree(path)


def get_valid_filename(name):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    """
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s)
    if s in {'', '.', '..'}:
        raise ValueError("Could not derive file name from '%s'" % name)
    return s


def get_page(b, url, xpath, t=20, delay=2):
    """
    :param b: selenium browser object
    :param url: url string to navigate to
    :param xpath: html element to wait for before considering the page loaded
    :param t: how long to wait before timing out (in seconds)
    :param delay: extra time to sleep (in seconds)
    :return:
    """
    b.get(url)

    try:
        WebDriverWait(b, t).until(ec.visibility_of_element_located((By.XPATH, xpath)))
    except TimeoutException:
        print("Timed out waiting for page to load")
        return -1

    time.sleep(delay)


def crawl_user(driver, user, output_dir="", max_pages=0, overwrite=True):
    baseurl = "https://www.thingiverse.com/" + user + "/designs?per_page=20&sort=newest"
    page_num = 1
    suburl = f"&page={page_num}"
    xpath = "//div[@class='Pagination__pageNumberWrapper--1Sao8']"

    if os.path.exists("thing_ids.txt"):
        if overwrite:
            os.remove("thing_ids.txt")
        else:
            print(str(Path(output_dir, "thing_ids.txt")) + " already exists and overwrite is False. Stopping.")
            return 0

    f = open(Path(output_dir, "thing_ids.txt"), "w")

    thing_ids = set()
    while True:
        print(baseurl + suburl)
        print(f'  page: {page_num}\n  loading...')
        get_page(driver, baseurl + suburl, xpath)

        # Load user page
        html = driver.page_source
        soup = BeautifulSoup(str(html), 'html.parser')

        # Get designs on page
        design_list = soup.find("div", {'class': re.compile('^UserDesigns__designsList.*')})
        designs = design_list.find_all("a", {'class': re.compile('^ThingCardBody__cardBodyWrapper.*')})

        # Take all designs, get their URLs, and split them down to just the thing id
        things = set([design['href'].split(":")[2] for design in designs])

        # Add newly found designs to a set and write the unique designs to a file
        if len(things) > 0:
            print(f'  found {len(things.difference(thing_ids))} things!\n')
            for thing in things.difference(thing_ids):
                f.write(str(thing)+"\n")
            thing_ids.update(things)
        else:
            print("\nNo more pages to load.")
            break

        if page_num >= max_pages > 0:
            print("\nMax page number reached.")
            break

        page_num += 1
        suburl = f"&page={page_num}"

    print("\nDone crawling user!")


def scrape_thing(driver, thing_id, output_dir="", redownload=False):
    baseurl = "https://www.thingiverse.com/thing:"
    thing_url = baseurl+thing_id
    xpath = "//ul[@class='thumbs animated']"

    get_page(driver, thing_url, xpath, delay=0)

    html = driver.page_source
    thing_files = driver.find_element(By.XPATH, ".//div[contains(text(), 'Thing Files')]")
    thing_files.click()
    html2 = driver.page_source

    # Load thing page
    soup = BeautifulSoup(str(html), 'html.parser')

    # Get title of thing and create filesystem friendly file name
    print('Checking thing name... ', end="")
    title = soup.find("div", {'class': re.compile('^ThingPage__modelName.*')}).text
    folder = get_valid_filename(title)
    thing_path = Path(output_dir + "/" + folder)

    if os.path.exists(thing_path) and not redownload:
        print(f"[X]\nFolder '{thing_path}' already exists. Skipping...")
    else:
        if redownload:  # Deletes contents of existing thing folder if redownload is enabled
            del_folder_contents(thing_path)
        create_dir(thing_path)

        print('[OK]\nScraping description... ', end="")
        # Scrape the summary and print settings
        summary = soup.find_all("div", {'class': re.compile('^ThingPage__description.*')})  # Locate summary
        print_settings = soup.find("div", {'class': re.compile('^ThingPage__preHistory.*')})  # Locate print settings
        print_settings = print_settings.find_all("p", {'class': re.compile('^ThingPage__description.*')})
        description = "Summary:\n"

        # Format text
        for txt in summary:
            description += txt.text.replace("\\r\\n', b'", "\n")
        description += "\nPrint Settings:\n"
        for txt in print_settings:
            description += txt.text + "\n"

        # Write the description to a file
        with open(Path(thing_path, "description.txt"), "w+") as f:
            f.write(description)
        print('[OK]\nScraping images... ', end="")

        # Scrape images
        images = soup.find("ul", "thumbs animated").find_all("img")

        # Create an 'images' folder if images were found
        if len(images) > 0:
            create_dir(Path(thing_path, "images"))

        # Loop over found images, download and enumerate them
        for i, image in enumerate(images):
            # Only download files from Thingiverse. This filters out YouTube links.
            if "cdn.thingiverse.com" in image["src"]:
                r = requests.get(image["src"])

                img_file = Path(thing_path, 'images', str(i)+Path(image["src"]).suffix.lower())
                if not os.path.exists(img_file) or redownload:
                    if r.status_code == 200:
                        with open(img_file, 'wb+') as f:
                            for chunk in r.iter_content(1024):
                                f.write(chunk)
        print("[OK]\nScraping files... ", end="")

        # Go to "Thing Files" page to scrape the stl download links
        soup2 = BeautifulSoup(str(html2), 'html.parser')
        stl_buttons = soup2.find_all("a", {'class': re.compile('^ThingFile__download.*')})  # Locate download URLs
        if len(stl_buttons) > 0:  # Only make "files" folder if download URLs are found
            create_dir(Path(thing_path, "files"))

        # Loop over found download URLs, download them and assign them their file names
        for download in stl_buttons:
            r = requests.get(download['href'])  # URL
            model_file = Path(thing_path, 'files', download['download'])  # File name
            if not os.path.exists(model_file) or redownload:
                if r.status_code == 200:
                    with open(model_file, 'wb+') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)

        print("[OK]")
