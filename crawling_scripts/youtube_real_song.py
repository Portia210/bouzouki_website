import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument('--headless')  # Enable headless mode
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
chrome_options.add_argument("accept-language=en-US;q=0.8,en;q=0.7")
# prefs = {'download.default_directory': download_dir}
# chrome_options.add_experimental_option('prefs', prefs)
driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()


def wait_for_element(css_selector, father_element=None):
    wait_element = father_element if father_element else driver

    return WebDriverWait(wait_element, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )

def youbube_video_exist(json_data, artist_name, song_name):
    if artist_name in json_data and song_name in json_data[artist_name]:
        video_url = json_data[artist_name][song_name]["youtube_video"]
        if video_url != "":
            return True
    return False

with open("youtube_songs.json", "r") as file:
    imported_json = json.load(file)

for artist_name, artist_data in imported_json.items():
    for song_name, song_dict in artist_data.items():
        if youbube_video_exist(imported_json, artist_name, song_name):
            continue
        youtube_query = f"{artist_name} {song_name}".replace(" ", "+")
        youtube_request_url = f"https://www.youtube.com/results?search_query={youtube_query}"
        driver.get(youtube_request_url)
        time.sleep(1)
        video_card = wait_for_element("ytd-video-renderer")
        video_link = video_card.find_element(By.CSS_SELECTOR, "a#thumbnail").get_attribute("href")
        song_dict["youtube_video"] = video_link
        song_dict["more_videos"] = youtube_request_url

        # Save the updated JSON data to a new file
        with open("youtube_songs.json", "w") as json_file:
            json.dump(imported_json, json_file, indent=4)



driver.close()
driver.quit()