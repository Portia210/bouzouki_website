from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from classes import import_db
from dotenv import load_dotenv
import os
load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
Bootstrap5(app)


@app.route("/")
def home():
    all_artists = import_db()
    all_artists = sorted(all_artists, key=lambda x: x.number_of_songs, reverse=True)
    # Fetch all movies and sort them by rating
    return render_template("index.html", all_artists= all_artists)


@app.route("/artist/<artist_name>")
def artist_songs(artist_name):
    all_artists = import_db()
    artist = [artist for artist in all_artists if artist.en_name == artist_name][0]
    print(artist)
    return render_template("artist_songs.html", artist=artist)




if __name__ == '__main__':
    app.run(debug=True)
