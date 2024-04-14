import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

download_dir = "C:\\Users\\yybar\\Downloads"
python_download_dir = "C:\\Users\\yybar\\Downloads\\python-downloads"

# set the driver
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


def wait_for_element(css_selector, father_element=None):
    wait_element = father_element if father_element else driver

    return WebDriverWait(wait_element, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )


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
driver.get("https://www.patreon.com/Partitourabouz/collections")

while True:
    start_collection_boxes = driver.find_elements(By.CSS_SELECTOR, 'a[data-tag="box-collection-href"]')
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    collection_boxes = driver.find_elements(By.CSS_SELECTOR, 'a[data-tag="box-collection-href"]')
    if len(start_collection_boxes) == len(collection_boxes):
        break

collections_data = []
for collection_box in collection_boxes:
    collection_title = collection_box.find_element(By.CSS_SELECTOR, 'p[data-tag="box-collection-title"]').text
    collection_href = f"https://www.patreon.com/Partitourabouz/collections{collection_box.get_attribute('href')}"
    collection_songs_number = collection_box.find_element(By.CSS_SELECTOR, 'p[data-tag="box-collection-num-post"]').text
    collection_data = {
        "title": collection_title,
        "href": collection_href,
        "songs_number": collection_songs_number
    }
    collections_data.append(collection_data)

file_path = "collections.json"

# Write collections data to the JSON file
with open(file_path, "w") as json_file:
    json.dump(collections_data, json_file, indent=4)

# driver.close()
# driver.quit()
