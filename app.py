from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
import sqlite3


class Artist:
    def __init__(self, artist_id, gr_name, en_name, number_of_songs, songs):
        self.artist_id = artist_id
        self.gr_name = gr_name
        self.en_name = en_name
        self.number_of_songs = number_of_songs
        self.songs = songs

    def __str__(self):
        return f"{self.gr_name} {self.en_name} {self.number_of_songs}"
    
class Song:
    def __init__(self, artist_id, gr_name, en_name, video_id, demo_id):
        self.gr_name = gr_name
        self.en_name = en_name
        self.video_id = video_id
        self.demo_id = demo_id
        self.artist_id = artist_id

    def __str__(self):
        return f"{self.gr_name} {self.en_name} {self.video_id} {self.demo_id} {self.artist_id}"
    

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
        # song columns are: id	artist_id	original_name	en_name	gr_name	video_id	demo_id	more_videos
        # convert demo_id and video_id to youtube links
        artist_songs = [Song(song[1], song[2], song[3], song[5], song[6]) for song in db_songs if song[1] == artist[0]]
        artist = Artist(artist[0], artist[2], artist[1], artist[3], artist_songs)
        artists.append(artist)
    
    return artists


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


@app.route("/")
def home():
    all_artists = import_db()
    all_artists = sorted(all_artists, key=lambda x: x.number_of_songs, reverse=True)
    # Fetch all movies and sort them by rating
    return render_template("index.html", all_artists= all_artists)


@app.route("/artist/<artist_id>")
def artist_songs(artist_id):
    all_artists = import_db()
    artist = [artist for artist in all_artists if artist.artist_id == int(artist_id)][0]
    print(artist)
    return render_template("artist_songs.html", artist=artist)




if __name__ == '__main__':
    app.run(debug=True)
