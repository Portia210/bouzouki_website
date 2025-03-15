import json

# artist dict(greek) > songs dict > song  dict

def search_song(text):
    with open("crawling_scripts/youtube_songs.json", "r") as file:
        imported_json = json.load(file)

    # /ΑΝΤΩΝΗΣ ΚΑΤΙΝΑΡΗΣ/songs/ΤΙ ΝΑ ΣΟΥ ΚΑΝΕΙ ΜΙΑ ΚΑΡΔΙΑ
    text = text.lower() 
    # print(song_name)
    for artist_value in imported_json.values():
        for song_name, song_value in artist_value["songs"].items():
            if text in song_name.lower() or text in song_value["song_en_name"].lower():
                print(song_value["song_en_name"])
                print(f"https://www.youtube.com/watch?v={song_value["demo_id"]}")

def count_songs():
    with open("crawling_scripts/youtube_songs.json", "r") as file:
        imported_json = json.load(file)

    all_songs =[]
    for artist_value in imported_json.values():
        artist_songs = artist_value["songs"].keys()
        all_songs.extend(artist_songs)
    return len(all_songs)

