import json
# import requests
# from bs4 import BeautifulSoup
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)
# chrome_options.add_argument('--headless')  # Enable headless mode
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
chrome_options.add_argument("accept-language=en-US;q=0.8,en;q=0.7")
# prefs = {'download.default_directory': download_dir}
# chrome_options.add_experimental_option('prefs', prefs)
driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()


def construct_url_with_params(base_url, params):
    encoded_params = "&".join([f"{key}={value}" for key, value in params.items()])
    return f"{base_url}?{encoded_params}"


def wait_for_element(css_selector, father_element=None):
    wait_element = father_element if father_element else driver

    return WebDriverWait(wait_element, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )


def youtube_video_exist(json_data, artist_name, song_name):
    if artist_name in json_data and song_name in json_data[artist_name]:
        video_url = json_data[artist_name][song_name]["youtube_video"]
        if video_url != "":
            return True
    return False


with open("collections.json", "r") as file:
    imported_json = json.load(file)

# for artist_name, artist_data in imported_json.items():
#     for song_name, song_dict in artist_data.items():
#         if youbube_video_exist(imported_json, artist_name, song_name):
#             continue
#         youtube_query = f"{artist_name} {song_name}".replace(" ", "+")
#         youtube_request_url = f"https://www.youtube.com/results?search_query={youtube_query}"
#         driver.get(youtube_request_url)
#         time.sleep(1)
#         video_card = wait_for_element("ytd-video-renderer")
#         video_link = video_card.find_element(By.CSS_SELECTOR, "a#thumbnail").get_attribute("href")
#         song_dict["youtube_video"] = video_link
#         song_dict["more_videos"] = youtube_request_url
#
#         # Save the updated JSON data to a new file
#         with open("youtube_songs.json", "w") as json_file:
#             json.dump(imported_json, json_file, indent=4)


# list 1
driver.get('https://www.patreon.com/login')
time.sleep(1)
driver.find_element(By.NAME, "email").send_keys("yehonatan11barhen@gmail.com")
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
time.sleep(0.5)
driver.find_element(By.NAME, "current-password").send_keys("Portia210")
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
time.sleep(1)

auth_element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "h2.sc-iqseJM.ggHibI"))
)

for collection in imported_json:
    if collection["img_url"] != "":
        continue
    driver.get(collection["href"])
    img_url = wait_for_element(".sc-fs4aqn-0").get_attribute("src")
    collection["img_url"] = img_url

    with open("collections.json", "w") as file:
        json.dump(imported_json, file, indent=4)

driver.close()
driver.quit()

