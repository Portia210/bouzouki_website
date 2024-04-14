import json
import os.path
import time
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from crawling_functions import *
from dowload_link import *


def crawl_more_pages(artist_path, one_card: WebElement):
    more_songs_link_container = try_to_find_element(one_card, '.sc-cfnzm4-0.kJujbw')
    if not more_songs_link_container:
        return None
    more_songs_links = more_songs_link_container.find_elements(By.CSS_SELECTOR, "a")
    more_songs_hrefs = [link.get_attribute("href") for link in more_songs_links if
                        "https://www.patreon.com/posts" in link.get_attribute("href")]
    for href in more_songs_hrefs:
        driver.get(href)
        new_page_post_card = wait_for_element(driver, '[data-tag="post-card"]')
        if new_page_post_card:
            crawl_one_card(artist_path, new_page_post_card)


def crawl_one_card(artist_path, one_card):
    song_name_element = try_to_find_element(one_card, '[data-tag="post-title"]', "no post title")
    if not song_name_element:
        return None
    song_name = song_name_element.text.split("-")[0].rstrip()
    song_path = os.path.join(artist_path, song_name)

    start_iframe_btn = try_to_find_element(one_card, '[title="Start playback"]')
    post_links_container = try_to_find_element(one_card, '[data-tag="post-attachments"]')
    txt_file_path = os.path.join(song_path, f"{song_name} video link.txt")
    if not os.path.exists(song_path):
        os.makedirs(song_path)
        print(f"created folder for {song_name} in {collection_name}")

    if start_iframe_btn and not os.path.exists(txt_file_path):
        # creating folder when there is iframe
        start_iframe_btn.click()
        iframe_link = wait_for_element(one_card, "iframe").get_attribute("src")
        video_id = urlparse(iframe_link).path.split("/")[-1]
        youtube_link = f"https://www.youtube.com/watch?v={video_id}"
        # print(f"Video id {video_id}\nYoutube link {youtube_link}")
        with open(txt_file_path, 'w', encoding="utf-8") as file:
            file.write(f"{song_name}\nVideo Link: {youtube_link}")

    if post_links_container:
        post_links = post_links_container.find_elements(By.CSS_SELECTOR, '[data-tag="post-attachment-link"]')
        for post_link in post_links:
            link_text = post_link.text
            if "xml" in post_link.text:
                continue
            file_path = os.path.join(song_path, link_text)
            if os.path.exists(file_path):
                continue

            # print(f"clicked on {link_text}")
            post_link.click()
            download_file_path = wait_for_new_file(download_dir)
            download_file_name = os.path.basename(download_file_path)
            if download_file_name != link_text:
                print(f"rename file from {download_file_name} to {link_text}")
            os.rename(download_file_path, file_path)
    os.rmdir(song_path) if not os.listdir(song_path) else None



with open("collections.json", "r") as file:
    collections_json = json.load(file)

download_dir = "C:\\Users\\yybar\\Downloads\\python-downloads"

driver = set_chrome_driver(download_dir)
login_to_patreon(driver)


for collection_data in collections_json:
    if collection_data["download"] not in ["waiting"]:
        continue
    collection_name = collection_data["title"]
    collection_path = os.path.join(download_dir, collection_name)
    if not os.path.exists(collection_path):
        os.makedirs(collection_path)
        print(f"created folder for {collection_name}")

    driver.get(collection_data["href"])
    # wait for first post card
    wait_for_element(driver, '[data-tag="post-card"]')

    post_cards = driver.find_elements(By.CSS_SELECTOR, '[data-tag="post-card"]')
    post_cards_len = 0
    while True:
        for post_card in post_cards[post_cards_len::]:
            more_pages_crawler = crawl_more_pages(collection_path, post_card)
            driver.get(collection_data["href"]) if more_pages_crawler else None
            post_card = wait_for_element(driver, '[data-tag="post-card"]')
            crawl_one_card(collection_path, post_card)

        post_cards_len = len(post_cards)
        load_more_btn = try_to_find_element(driver, ".sc-iCfMLu.cRkIlM")
        if load_more_btn:
            load_more_btn.click()
        else:
            break

        new_post_cards_len = post_cards_len
        while new_post_cards_len == post_cards_len:
            time.sleep(2)
            post_cards = driver.find_elements(By.CSS_SELECTOR, '[data-tag="post-card"]')
            new_post_cards_len = len(post_cards)

    collection_data["download"] = "finished"
    with open("collections.json", "w") as file:
        json.dump(collections_json, file, indent=4)
        print(f"---------------{collection_data["title"]} finished ---------------")


