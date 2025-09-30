import sqlite3

class Artist:
    def __init__(self, en_name, gr_name, number_of_songs, artist_img, songs):
        self.gr_name = gr_name
        self.en_name = en_name
        self.number_of_songs = number_of_songs
        self.artist_img = artist_img
        self.songs = songs

    def __str__(self):
        return f"{self.gr_name} {self.en_name} {self.number_of_songs} {self.songs}"
    
class Song:
    def __init__(self, artist_name, en_name, gr_name, video_id, demo_id):
        self.artist_name = artist_name
        self.gr_name = gr_name
        self.en_name = en_name
        self.video_id = video_id
        self.demo_id = demo_id

    def __str__(self):
        return f"{self.artist_name} {self.gr_name} {self.en_name} {self.video_id} {self.demo_id}"
    
def import_db():
    conn = sqlite3.connect('instance/music.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM artists")
    db_artists = cursor.fetchall()
    cursor.execute("SELECT * FROM songs")
    db_songs = cursor.fetchall()
    conn.close()

    artists = []
    for artist in db_artists:
        # artist columns are: artist_id	en_name	gr_name	number_of_songs	artist_img
        # song columns are: song_id	artist_name	en_name	gr_name	video_id	demo_id
        artist_songs = [Song(song[1], song[2], song[3], song[4], song[5]) for song in db_songs if song[1] == artist[1]]
        artist = Artist(artist[1], artist[2], artist[3], artist[4], artist_songs)
        artists.append(artist)
    return artists