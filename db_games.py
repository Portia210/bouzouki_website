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
    for artist in artists:
        # get the artist image from wikipedia
        google_imgs_url = f"https://www.google.com/search?hl=en&tbm=isch&q={artist}"
        wikipedia_url = f"https://el.wikipedia.org/w/index.php?fulltext=1&search={artist}&ns0=1"
        driver.get(wikipedia_url)

        time.sleep(2)
        input("Press Enter to continue...")
        # Get the first image
        first_img = automation.safe_find(By.CSS_SELECTOR, ".infobox img", 1)
        if first_img:
            src = first_img.get_attribute("src")
            driver.get(src)
            img = driver.find_element(By.CSS_SELECTOR, 'img').screenshot_as_png

            with open(f"{artist}.png", "wb") as file:
                file.write(img)
            # Store the image in the database
            store_img_in_db(f"{artist}.png", db, table, artist)


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
