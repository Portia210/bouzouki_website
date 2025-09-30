import sqlite3
from logger import logger

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
    """Import artists and songs from SQLite database with error handling"""
    conn = None
    try:
        logger.info("Attempting to connect to database")

        # Check if database file exists
        db_path = 'instance/music.db'
        if not sqlite3.connect(db_path).execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            logger.error(f"Database {db_path} appears to be empty or corrupted")
            return []

        conn = sqlite3.connect(db_path, timeout=10.0)  # Add timeout
        cursor = conn.cursor()

        # Execute queries with error handling
        logger.debug("Fetching artists from database")
        cursor.execute("SELECT * FROM artists")
        db_artists = cursor.fetchall()
        logger.info(f"Found {len(db_artists)} artists")

        logger.debug("Fetching songs from database")
        cursor.execute("SELECT * FROM songs")
        db_songs = cursor.fetchall()
        logger.info(f"Found {len(db_songs)} songs")

        artists = []
        for artist in db_artists:
            try:
                # artist columns are: artist_id	en_name	gr_name	number_of_songs	artist_img
                # song columns are: song_id	artist_name	en_name	gr_name	video_id	demo_id
                artist_songs = [
                    Song(song[1], song[2], song[3], song[4], song[5])
                    for song in db_songs if song[1] == artist[1]
                ]
                artist_obj = Artist(artist[1], artist[2], artist[3], artist[4], artist_songs)
                artists.append(artist_obj)
            except Exception as e:
                logger.error(f"Error processing artist {artist[1] if len(artist) > 1 else 'unknown'}: {e}")
                continue

        logger.info(f"Successfully processed {len(artists)} artists")
        return artists

    except sqlite3.OperationalError as e:
        logger.error(f"Database operational error: {e}")
        return []
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error: {e}")
        return []
    except FileNotFoundError:
        logger.error("Database file not found: instance/music.db")
        return []
    except Exception as e:
        logger.error(f"Unexpected error importing database: {e}")
        return []
    finally:
        if conn:
            try:
                conn.close()
                logger.debug("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")