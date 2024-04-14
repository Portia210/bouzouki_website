import json
from urllib.parse import urlparse, parse_qs
from crawling_functions import *


with open("youtube_songs.json", "r") as file:
    imported_json = json.load(file)

with open("collections.json", "r") as file:
    imported_collections = json.load(file)

# driver = set_chrome_driver()
counter = 0
for collection in imported_collections:

    imported_json[collection["title"]]["img_url"] = collection["img_url"]
with open("youtube_songs.json", "w") as file:
    json.dump(imported_json, file, indent=4)


#
# for collection_data in imported_json:
#     if collection_data["download"] == "finished":
#         collection_data["download"] = ""
#     else:
#         collection_data["download"] = "finished"
#
# with open("collections.json", "w") as file:
#     json.dump(imported_json, file, indent=4)
