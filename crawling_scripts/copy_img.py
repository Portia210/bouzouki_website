import json

# Open the JSON file for reading
with open('collections.json', 'r') as file:
    # Load the JSON data
    collections = json.load(file)

with open('youtube_songs.json', 'r') as file:
    # Load the JSON data
    youtube_songs = json.load(file)

for collection in collections:
    artist_name = collection['title']  # Access the value associated with the 'href' key

    if artist_name in youtube_songs:
        youtube_songs[artist_name]["img_url"] = collection["img_url"]
        # print(youtube_songs[artist_name]["img_url"])

# for key, artist in youtube_songs.items():
#     youtube_songs[key] = {
#         "img_url": "",
#         "songs": artist
#     }



# Write collections data to the JSON file
with open("youtube_songs.json", "w") as file:
    json.dump(youtube_songs, file, indent=4)
