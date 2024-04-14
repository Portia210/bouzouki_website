import json
import time
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_v_parameter(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    v_value = query_params.get('v')
    return v_value[0] if v_value else None


def title_greek(input_str):
    # Split the input string into words
    words = input_str.split()
    # Capitalize the first character of each word and convert the rest to lowercase
    modified_words = [word[0].upper() + word[1:].lower() for word in words]
    # Join the modified words back together into a single string
    return ' '.join(modified_words)


def construct_url_with_params(base_url, params):
    encoded_params = "&".join([f"{key}={value}" for key, value in params.items()])
    return f"{base_url}?{encoded_params}"


def wait_for_element(css_selector, father_element=None):
    wait_element = father_element if father_element else driver
    element = None
    try:
        element = WebDriverWait(wait_element, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
    except TimeoutException:
        print("element doesn't found")
    return element


def youtube_video_exist(json_data, artist_name, song_name):
    if artist_name in json_data and song_name in json_data[artist_name]:
        video_url = json_data[artist_name][song_name]["youtube_video"]
        if video_url != "":
            return True
    return False


def move_songs_to_last(dictionary):
    if "songs" in dictionary:
        songs_value = dictionary.pop("songs")
        dictionary["songs"] = songs_value
    return dictionary


def login_to_patreon():
    driver.get('https://www.patreon.com/login')
    time.sleep(1)
    driver.find_element(By.NAME, "email").send_keys("yehonatan11barhen@gmail.com")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(0.5)
    driver.find_element(By.NAME, "current-password").send_keys("Portia210")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h2.sc-iqseJM.ggHibI"))
    )
    return "log in to patreon successfully"


def det_collection_img(json_file):
    """
    take the json file, and return the json file with image for each artist
    need to log in first to Patreon
    """

    for collection in json_file:
        if collection["img_url"] != "":
            continue
        driver.get(collection["href"])
        img_url = wait_for_element(".sc-fs4aqn-0").get_attribute("src")
        collection["img_url"] = img_url
    return json_file


def greekish_name(json_file):
    """get the greekish name for each artist and song"""

    # full_list
    def translate_all_keys(dictionary, new_key_name):
        """take dictionary and new kay name to return the translations"""
        first_value = next(iter(dictionary.values()))
        if first_value[new_key_name] != "":
            return dictionary
        greek_list = "\n".join(dictionary.keys())
        text_area = driver.find_element(By.CSS_SELECTOR, "textarea#input")
        text_area.clear()
        text_area.send_keys(greek_list)
        time.sleep(0.1)
        submit_input = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
        submit_input.click()
        time.sleep(0.5)
        result = wait_for_element("div.result").text
        en_names_list = result.split("\n")
        counter = 0
        for song_name, song_data in dictionary.items():
            song_data[new_key_name] = en_names_list[counter].title()
            counter += 1
        return dictionary

    driver.get("https://greeklishconverter.com/")
    time.sleep(1)

    # translate every artist name to greekish
    json_file = translate_all_keys(json_file, "artist_en_name")
    # reverse artist_gr_name
    for artist_name, artist_data in json_file.items():
        old_name = artist_data["artist_gr_name"].split()
        new_name = ' '.join(reversed(old_name))
        artist_data["artist_gr_name"] = new_name

    # translate every song name to greekish
    for artist_name, artist_data in json_file.items():
        artist_data["songs"] = translate_all_keys(artist_data["songs"], "song_en_name")

    return json_file


def youtube_id_for_artist(json_file, artist_name):
    artist_data = json_file[artist_name]
    for song_name, song_data in artist_data["songs"].items():
        if ("video_id" in song_data and song_data["video_id"] != ""
                and song_data["video_id"] != song_data["demo_id"]):
            continue

        youtube_query = f"{artist_data["artist_gr_name"]} {song_name}".replace(" ", "+")
        youtube_request_url = f"https://www.youtube.com/results?search_query={youtube_query}&sp=CAM%253D"
        driver.get(youtube_request_url)
        time.sleep(0.2)
        renderer_first_element = wait_for_element("ytd-video-renderer")
        if not renderer_first_element:
            continue
        video_cards = driver.find_elements(By.TAG_NAME, "ytd-video-renderer")
        for video_card in video_cards:
            video_link = video_card.find_element(By.CSS_SELECTOR, "a#thumbnail").get_attribute("href")
            video_id = get_v_parameter(video_link)
            video_channel = video_card.text.split("\n")[3]
            if not video_id:
                print("no youtube id for video")
                continue
            elif video_channel == "Markos Kouvariotis":
                print("forbidden channel, continuing")
                continue
            else:
                song_data["video_id"] = video_id
                song_data["more_videos"] = youtube_request_url
                break

    return artist_data


def set_chrome_driver():
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
    return driver


driver = set_chrome_driver()

with open("youtube_songs.json", "r") as file:
    imported_json = json.load(file)

for artist_name, artist_data in imported_json.items():
    imported_json[artist_name] = youtube_id_for_artist(imported_json, artist_name)
    with open("youtube_songs.json", "w") as file:
        json.dump(imported_json, file, indent=4)
    print(f"{artist_name}   update")

driver.close()
driver.quit()
