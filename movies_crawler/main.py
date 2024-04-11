import time

from selenium import webdriver
from selenium.webdriver.common.by import By

# set the driver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument('--headless')  # Enable headless mode
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
chrome_options.add_argument("accept-language=en-US;q=0.8,en;q=0.7")
driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()

# list 1
# driver.get('https://www.bfi.org.uk/sight-and-sound/polls/greatest-films-all-time-2012')
# time.sleep(1)
#
# headlines = driver.find_elements(By.CSS_SELECTOR, ".Headline__H2-sc-e1fxl5-2.eKkqcD")
# text_list = ""
# for headline in headlines:
#     text_list += f"\n{headline.text}"
#     try:
#         description = driver.execute_script(
#             'return arguments[0].nextElementSibling', headline)
#         text_list += f"  - {description.text}"
#     except NoSuchElementException:
#         print("no description")
#
# with open(f"list.txt", 'w', encoding="utf-8") as file:
#     file.write(text_list)

# list 2
driver.get('https://www.empireonline.com/movies/features/best-movies-2/')
time.sleep(1)

movies_cards = driver.find_elements(By.CSS_SELECTOR, "div.listicle_listicle__item__CJna4")
text_list = ""
for movie_card in movies_cards[::-1]:
    headline = movie_card.find_element(By.CSS_SELECTOR, "h3.listicleItem_listicle-item__title__BfenH")
    img_link = movie_card.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
    text_list += f"\n{headline.text}\n{img_link}"

with open(f"list2.txt", 'w', encoding="utf-8") as file:
    file.write(text_list)

# list 3
# driver.get('https://www.imdb.com/list/ls058705802/')
# time.sleep(1)
#
#
# movies_cards = driver.find_elements(By.CSS_SELECTOR, ".lister-item-content")
# print(len(movies_cards))
# text_list = ""
# for movie_card in movies_cards[:100:]:
#     movie_name = movie_card.find_element(By.CSS_SELECTOR, "h3.lister-item-header")
#     movie_details = movie_card.find_element(By.XPATH, "./p")
#     movie_description = movie_card.find_element(By.XPATH, "./p[2]")
#     text_list += f"\n{movie_name.text}\n  - {movie_details.text}\n  - {movie_description.text}"
#
# with open(f"list3.txt", 'w', encoding="utf-8") as file:
#     file.write(text_list)
