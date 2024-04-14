import json
import os.path

from crawling_functions import *
from dowload_link import *


def crawl_more_pages(artist_path, one_card: WebElement):
    more_songs_link_container = try_to_find_element(one_card, '.sc-cfnzm4-0.kJujbw')
    if not more_songs_link_container:
        return None
    more_songs_links = more_songs_link_container.find_elements(By.CSS_SELECTOR, "a")
    if len(more_songs_links) == 0:
        return None
    more_songs_hrefs = [link.get_attribute("href") for link in more_songs_links if
                        "https://www.patreon.com/posts" in link.get_attribute("href")]
    for href in more_songs_hrefs:
        driver.get(href)
        new_page_post_card = wait_for_element(driver, '[data-tag="post-card"]')
        if new_page_post_card:
            crawl_one_card(artist_path, new_page_post_card, skip_iframe_btn=True)
    driver.get(collection_data["href"])
    wait_for_element(driver, '[data-tag="post-card"]')



def crawl_one_card(artist_path, one_card, skip_iframe_btn=False):
    song_name_element = try_to_find_element(one_card, '[data-tag="post-title"]', "no post title")
    if not song_name_element:
        return None
    song_name = song_name_element.text.split("-")[0].rstrip()
    song_name = replace_forbidden_chars(song_name)
    song_path = os.path.join(artist_path, song_name)

    start_iframe_btn = try_to_find_element(one_card, '[title="Start playback"]')

    post_links_container = try_to_find_element(one_card, '[data-tag="post-attachments"]')
    txt_file_path = os.path.join(song_path, f"{song_name} video link.txt")
    if not os.path.exists(song_path):
        os.makedirs(song_path)
        print(f"created folder for {song_name} in {collection_name}")

    # if start_iframe_btn:
    if start_iframe_btn and not os.path.exists(txt_file_path):
        # creating folder when there is iframe
        start_iframe_btn.click()
        iframe_element = wait_for_element(one_card, "iframe")
        iframe_link = iframe_element.get_attribute("src")
        video_id = urlparse(iframe_link).path.split("/")[-1]
        youtube_link = f"https://www.youtube.com/watch?v={video_id}"
        with open(txt_file_path, 'w', encoding="utf-8") as file:
            print("added text file")
            file.write(f"{song_name}\nVideo Link: {youtube_link}")
    if skip_iframe_btn:
        iframe_element = wait_for_element(one_card, "iframe")
        iframe_link = iframe_element.get_attribute("src")
        video_id = urlparse(iframe_link).path.split("/")[-1]
        youtube_link = f"https://www.youtube.com/watch?v={video_id}"
        with open(txt_file_path, 'w', encoding="utf-8") as file:
            print("added text file")
            file.write(f"{song_name}\nVideo Link: {youtube_link}")



    if post_links_container:
        post_links = post_links_container.find_elements(By.CSS_SELECTOR, '[data-tag="post-attachment-link"]')
        for post_link in post_links:
            link_text = post_link.text
            if "xml" in post_link.text:
                continue
            link_file_path = os.path.join(song_path, link_text)
            if os.path.exists(link_file_path):
                continue

            post_link.click()
            download_file_path = wait_for_new_file(download_dir)
            download_file_name = os.path.basename(download_file_path)
            if download_file_name != link_text:
                print(f"rename file from {download_file_name} to {link_text}")
            os.rename(download_file_path, link_file_path)
    os.rmdir(song_path) if not os.listdir(song_path) else None


with open("collections.json", "r") as file:
    collections_json = json.load(file)

download_dir = "C:\\Users\\yybar\\Downloads\\python-downloads"

driver = set_chrome_driver(download_dir)
login_to_patreon(driver)

for collection_data in collections_json:
    if collection_data["download"] =="finished":
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
            crawl_more_pages(collection_path, post_card)

            crawl_one_card(collection_path, post_card)

        post_cards_len = len(post_cards)
        load_more_btn = try_to_find_element(driver, "button .sc-iCfMLu.cRkIlM")
        if load_more_btn:
            print("---------------------------------------------------click more results button")
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

driver.close()
driver.quit()
