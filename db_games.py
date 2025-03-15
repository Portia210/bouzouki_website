import sqlite3
from automation import Automation
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd


def fetch_artists_names(driver, db_artists, automation):

    if not os.path.exists("artists.csv"):
        with open("artists.csv", "w", encoding="utf-8") as f:
            f.write("artist,main_title,english_title\n")

    with open("artists.csv", "r", encoding="utf-8") as f:
        csv_artists = f.readlines()
    csv_artists = [artist.split(",")[0] for artist in csv_artists[1:]]
    print(f"csv_artists = {csv_artists}")
    new_artists = [artist for artist in db_artists if artist not in csv_artists]
    (print(f"new_artists = {new_artists}"))

    for i, artist in enumerate(new_artists):
        driver.get(f"https://www.google.com/search?q={artist}")
        if i == 0:
            input("Press Enter to continue...")
        
        main_title = automation.safe_find(By.CSS_SELECTOR, 'div[data-attrid="title"]', 2)
        english_title = automation.safe_find(By.CSS_SELECTOR, 'div[data-attrid="title"] span[dir="ltr"]', 0.1)
        main_title_text = main_title.text if main_title else None
        english_title_text = english_title.text if english_title else None
        # substcut the english title from the main title
        if main_title_text and english_title_text:
            main_title_text = main_title_text.replace(english_title_text, "").strip()
        english_title_text = english_title_text.replace("(", "").replace(")", "") if english_title_text else None
        # write into csv file
        with open("artists.csv", "a",encoding="utf-8") as f:
            f.write(f"{artist},{main_title_text},{english_title_text}\n")




# function to remove from articts table the column called original_name
def remove_column(column_name):
    conn = sqlite3.connect('instance/music.db')
    cursor = conn.cursor()

    cursor.execute(f"ALTER TABLE artists DROP COLUMN {column_name}")

    conn.commit()
    conn.close()

def play_db():
    # Connect to the SQLite database
    conn = sqlite3.connect('instance/music.db')
    cursor = conn.cursor()

    csv_file = "artists.csv"    
    with open(csv_file, "r", encoding="utf-8") as f:
        csv_artists = f.readlines()
    csv_artists = [artist.split(",") for artist in csv_artists[1:]]

    # Close the connection
    conn.commit()
    conn.close()

    return 

def main():
    # count all songs in the db
    conn = sqlite3.connect('instance/music.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM songs")
    songs_count = cursor.fetchone()[0]
    print(f"songs_count = {songs_count}")
    conn.close()


import sqlite3
import os

def store_img_in_db(img_src, db_name, table_name):
    """Stores an image in an SQLite database as a BLOB."""
    
    # Ensure the database folder exists
    os.makedirs(os.path.dirname(db_name), exist_ok=True)

    # Connect to the database and create the table if it doesn’t exist
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            img BLOB NOT NULL
        )""")

        # Insert image into the table
        cursor.execute(f"INSERT INTO {table_name} (img) VALUES (?)", (sqlite3.Binary(img_src),))
        conn.commit()

        # Get the ID of the inserted image
        img_id = cursor.lastrowid

    print(f"Image stored in the database with ID {img_id}")
    return img_id  # Return ID for later retrieval

def retrieve_img_from_db(img_id, db_name, table_name):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT img FROM {table_name} WHERE id = ?", (img_id,))
        img = cursor.fetchone()[0]
        return img



if __name__ == "__main__":
    import json
    with open("jsons/youtube_songs.json", "r", encoding="utf-8") as f:
        all_data = json.load(f)
    
    # create 2 tables in instance/music.db
    with sqlite3.connect('instance/music.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS artists (
            artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            en_name TEXT NOT NULL,
            gr_name TEXT NOT NULL,
            number_of_songs INTEGER NOT NULL, 
            artist_img BLOB
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS songs (
            song_id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_name TEXT NOT NULL,
            en_name TEXT NOT NULL,
            gr_name TEXT NOT NULL,
            video_id TEXT NOT NULL,
            demo_id TEXT NOT NULL
        )""")
        conn.commit()

        for key, artist_data in all_data.items():
            en_name = artist_data["artist_en_name"]
            gr_name = artist_data["artist_gr_name"]
            number_of_songs = len(artist_data["songs"])
            cursor.execute("INSERT INTO artists (en_name, gr_name, number_of_songs) VALUES (?, ?, ?)", (en_name, gr_name, number_of_songs))


            for sogns_gr_name, song_data in artist_data["songs"].items():
                song_gr_name = sogns_gr_name.lower()
                sogns_en_name = song_data.get("song_en_name", "")
                video_id = song_data.get("video_id", "")
                demo_id = song_data.get("demo_id", "")
                print(f"gr_name = {gr_name}, sogns_en_name = {sogns_en_name}, video_id = {video_id}, demo_id = {demo_id}")
                cursor.execute("INSERT INTO songs (artist_name, en_name, gr_name, video_id, demo_id) VALUES (?, ?, ?, ?, ?)", (en_name, sogns_en_name, song_gr_name, video_id, demo_id))
        conn.commit()

