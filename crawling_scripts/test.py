import json
from urllib.parse import urlparse, parse_qs

with open("youtube_songs.json", "r") as file:
    imported_json = json.load(file)

for artist_name, artist_data in imported_json.items():
    for song_name, song_data in artist_data["songs"].items():

        song_data["video_id"] = ""
with open("youtube_songs.json", "w") as file:
    json.dump(imported_json, file, indent=4)
