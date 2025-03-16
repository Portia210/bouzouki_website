import sqlite3
from automation import Automation
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import urllib



def store_img_in_db(img_path, db_name, table_name, gr_name):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        with open(img_path, "rb") as file:
            img = file.read()
        cursor.execute(f"UPDATE {table_name} SET artist_img = ? WHERE gr_name = ?", (img, gr_name))
        conn.commit()

def retrieve_img_from_db(img_id, db_name, table_name):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT img FROM {table_name} WHERE id = ?", (img_id,))
        img = cursor.fetchone()[0]
        return img




def get_images_with_driver():
    db = "instance/music.db"
    table = "artists"
    # get artists from db that the artist_img is None
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(f"SELECT gr_name FROM {table} WHERE artist_img IS NULL")
    artists = cursor.fetchall()
    artists = [artist[0] for artist in artists]


    automation = Automation()
    driver = automation.start_chrome_driver()
    patreon_url = "https://www.patreon.com/c/partitourabouz/collections"
    driver.get(patreon_url)
    input("Press Enter to continue...")
    artists_cards = driver.find_elements(By.CSS_SELECTOR, ".sc-ieecCq.hlVSeb")
    images_dict = {}
    for _ in range(len(artists_cards)):
        artist_name_elem = automation.safe_find(By.CSS_SELECTOR, '.sc-ieecCq.hlVSeb [data-tag="box-collection-title-href"]',0.2)
        if artist_name_elem:
            artist_name = artist_name_elem.text
            artist_img_elem = automation.safe_find(By.CSS_SELECTOR, '.sc-ieecCq.hlVSeb [data-tag="box-collection-thumbnail"]',0.2)
            # get background-img url from artist_img_elem
            artist_img_url = artist_img_elem.value_of_css_property("background-image")
            if artist_img_url:
                artist_img_url = artist_img_url.replace('url("', "").replace('")', "")
                images_dict[artist_name] = artist_img_url

    for artist_name, artist_img_url in images_dict.items():
        try:
            driver.get(artist_img_url)
            driver.find_element(By.CSS_SELECTOR, "img").screenshot_as_png(f"images/{artist_name}.png")
            # with open (f"images/{artist_name}.png", "rb") as file:
            #     img = file.read()
            # store_img_in_db(img, db, table, artist_name)
        except Exception as e:
            print(e)
            continue





def delete_images():
    db = "instance/music.db"
    table = "artists"
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {table} SET artist_img = NULL")
    conn.commit()

if __name__ == "__main__":
    # delete_images()
    get_images_with_driver()
