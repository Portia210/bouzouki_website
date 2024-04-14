import time
from typing import Union
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def construct_url_with_params(base_url, params):
    encoded_params = "&".join([f"{key}={value}" for key, value in params.items()])
    return f"{base_url}?{encoded_params}"


def get_parameter_from_url(url, query="v"):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    v_value = query_params.get(query)
    return v_value[0] if v_value else None

def replace_forbidden_chars(string)->str:
    forbidden_chars = '<>:"/\\|?*'
    cleaned_string = ''
    for char in string:
        if char in forbidden_chars:
            cleaned_string += '_'
        else:
            cleaned_string += char
    return cleaned_string
def title_greek(input_str):
    words = input_str.split()
    modified_words = [word[0].upper() + word[1:].lower() for word in words]
    return ' '.join(modified_words)


def wait_for_element(father_element: Union[WebDriver, WebElement], css_selector, error_text="") -> Optional[WebElement]:
    """father could be or driver or another element"""
    try:
        element = WebDriverWait(father_element, 8).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )
        return element
    except TimeoutException:
        print(error_text) if error_text else None
        return None


def try_to_find_element(father_element: Union[WebDriver, WebElement], css_selector, error_text="") -> Optional[
    WebElement]:
    """father could be or driver or another element"""
    try:
        element = father_element.find_element(By.CSS_SELECTOR, css_selector)
        return element
    except NoSuchElementException:
        print(error_text) if error_text else None
        return None
    except Exception as e:
        # Handle other exceptions here
        print("element no found")
        return None


def move_songs_to_last(dictionary):
    if "songs" in dictionary:
        songs_value = dictionary.pop("songs")
        dictionary["songs"] = songs_value
    return dictionary


def login_to_patreon(driver):
    driver.get('https://www.patreon.com/login')
    wait_for_element(driver, '[name="email"]').send_keys("yehonatan11barhen@gmail.com")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait_for_element(driver, '[name="current-password"]').send_keys("Portia210")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(0.5)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h2.sc-iqseJM.ggHibI"))
    )
    print("log in to patreon successfully")


def greekish_name(driver, json_file):
    """get the greekish name for each artist and song"""

    # full_list
    def translate_all_keys(dictionary, new_key_name):
        """take dictionary and new kay name to return the translations"""
        greek_list = "\n".join(dictionary.keys())
        text_area = driver.find_element(By.CSS_SELECTOR, "textarea#input")
        text_area.clear()
        text_area.send_keys(greek_list)
        time.sleep(0.1)
        submit_input = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
        submit_input.click()
        time.sleep(0.5)
        result = wait_for_element(driver, "div.result").text
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


def youtube_id_for_artist(driver, json_file, artist_name):
    artist_data = json_file[artist_name]
    for song_name, song_data in artist_data["songs"].items():
        if ("video_id" in song_data and song_data["video_id"] != ""
                and song_data["video_id"] != song_data["demo_id"]):
            continue

        youtube_query = f"{artist_data["artist_gr_name"]} {song_name}".replace(" ", "+")
        youtube_request_url = f"https://www.youtube.com/results?search_query={youtube_query}&sp=CAM%253D"
        driver.get(youtube_request_url)
        time.sleep(0.2)
        renderer_first_element = wait_for_element(driver, "ytd-video-renderer")
        if not renderer_first_element:
            print(f"no videos found for {song_data["song_en_name"]}")
            continue
        video_cards = driver.find_elements(By.TAG_NAME, "ytd-video-renderer")
        for video_card in video_cards:
            video_link = video_card.find_element(By.CSS_SELECTOR, "a#thumbnail").get_attribute("href")
            video_id = get_parameter_from_url(video_link)
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


def set_chrome_driver(download_dir=None) ->WebDriver:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)
    # chrome_options.add_argument('--headless')  # Enable headless mode
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    chrome_options.add_argument("accept-language=en-US;q=0.8,en;q=0.7")
    if download_dir:
        chrome_options.add_experimental_option('prefs', {'download.default_directory': download_dir})
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver
