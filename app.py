from flask import Flask, render_template, request, jsonify
from flask_bootstrap import Bootstrap5
from classes import import_db
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key")
Bootstrap5(app)

# Global variable to store all artists
all_artists = import_db()

@app.route("/")
def home():
    # Sort artists by the number of songs
    sorted_artists = sorted(all_artists, key=lambda x: x.number_of_songs, reverse=True)
    return render_template("index.html", all_artists=sorted_artists)


@app.route("/artist/<artist_name>")
def artist_songs(artist_name):
    # Use a dictionary for efficient artist lookup
    artist = next((artist for artist in all_artists if artist.en_name == artist_name), None)
    if artist:
        return render_template("artist_songs.html", artist=artist)
    else:
        return render_template("404.html"), 404  # Handle case when artist is not found


@app.route("/search", methods=["GET"])
def search_songs():
    term = request.args.get("term")  # Get the search term from the query string
    if not term:
        return jsonify([])  # Return empty list if no term is provided
    
    results = []

    # Fetch all artists from the database
    all_artists = import_db()
    
    if not all_artists:
        return jsonify([])  # Return empty list if no artists were found
    
    for artist in all_artists:
        for song in artist.songs:
            # Check if the term is in either the English or Greek song name
            if term.lower() in song.en_name.lower() or term.lower() in song.gr_name.lower():
                results.append({
                    'label': song.en_name,  # Display song name
                    'value': song.en_name,
                    'url': f"/song/{song.en_name}"  # Redirect URL
                })
    
    return jsonify(results)


@app.route("/song/<song_name>")
def view_song(song_name):
    # Fetch all artists from the database
    all_artists = import_db()
    
    # Find the song from the list of artists
    song = None
    for artist in all_artists:
        for s in artist.songs:
            if s.en_name == song_name:
                song = s
                artist_obj = artist  # Keep track of the artist object
    
    if not song:
        return "Song not found", 404  # In case the song is not found

    return render_template("song_details.html", artist=artist_obj, song=song)



# if __name__ == '__main__':
#     app.run()
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Get PORT from environment
    app.run(host="0.0.0.0", port=port)