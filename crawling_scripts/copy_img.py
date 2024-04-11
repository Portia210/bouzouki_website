import json

# Open the JSON file for reading
with open('collections.json', 'r') as file:
    # Load the JSON data
    collections = json.load(file)

with open('youtube_songs.json', 'r') as file:
    # Load the JSON data
    youtube_songs = json.load(file)

for key, artist in youtube_songs.items():
    for song_k, song in artist["songs"].items():
        song["video_id"] = song["youtube_video"].split("watch?v=")[1]
        song["demo_id"] = song["demo_youtube_url"].split("watch?v=")[1]

# Write collections data to the JSON file
with open("youtube_songs.json", "w") as file:
    json.dump(youtube_songs, file, indent=4)
