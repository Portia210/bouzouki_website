import json
import os


def song_folder_exist(json_data, artist_name, song_name):
    if artist_name in json_data and song_name in json_data[artist_name]:
        # video_url = json_data[artist_name][song_name]["youtube_video"]
        # if video_url != "":
        #     print(video_url)
        return True
    return False


python_download_dir = "C:\\Users\\yybar\\Downloads\\python-downloads"

# Get the list of files in the directory
artists_libraries = os.listdir(python_download_dir)

# imported_json = {}
with open("youtube_songs.json", "r") as json_file:
    imported_json = json.load(json_file)

for artist_library in artists_libraries:
    artist_library_path = os.path.join(python_download_dir, artist_library)
    if os.path.isdir(artist_library_path):
        songs_library = os.listdir(artist_library_path)
        artist_dict = {}
        for song_library in songs_library:
            if song_folder_exist(imported_json, artist_library, song_library):
                continue
            song_library_path = os.path.join(artist_library_path, song_library)
            if os.path.isdir(song_library_path):
                if not os.listdir(song_library_path):
                    # If the folder is empty, remove it
                    os.rmdir(song_library_path)
                    continue

                txt_file_path = os.path.join(song_library_path, f"{song_library} video link.txt")
                if os.path.isfile(txt_file_path):
                    # Open the text file and print the URL
                    with open("video link.txt", 'r', encoding="utf-8") as txt_file:
                        # Skip the first line by calling readline()
                        link_line = txt_file.readlines()[1]
                        youtube_url = link_line.split(": ")[1]
                        song_dict = {
                            "demo_youtube_url": youtube_url,
                            "youtube_video": "",
                            "more_videos": ""
                        }
                        artist_dict[song_library] = song_dict
                else:
                    print("No text file found in", txt_file_path)
            imported_json[artist_library] = artist_dict

# print(imported_json)
with open("youtube_songs.json", "w") as json_file:
    json.dump(imported_json, json_file, indent=4)
