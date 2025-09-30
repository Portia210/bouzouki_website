# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based bouzouki music website that displays Greek traditional music artists and their songs. The application serves as a catalog for bouzouki music with artist profiles, song details, and media integration.

## Key Architecture

### Core Components
- **Flask Application** (`app.py`): Main web server with routes for home, artist pages, song details, and search
- **Data Models** (`classes.py`): Artist and Song classes with SQLite database integration via `import_db()`
- **Database**: SQLite databases in `instance/` directory:
  - `music.db`: Main database with artists and songs tables
  - `images.db`: Stores artist images as binary data
- **Templates**: Jinja2 HTML templates in `templates/` using Bootstrap5
- **Static Assets**: CSS, JavaScript, and images in `static/` directory

### Database Schema
- **Artists table**: artist_id, en_name, gr_name, number_of_songs, artist_img (binary)
- **Songs table**: song_id, artist_name, en_name, gr_name, video_id, demo_id

### Data Flow
1. `import_db()` loads all artists and songs from SQLite into memory
2. Artists are sorted by song count on homepage
3. Search functionality queries loaded data for song matches
4. Dynamic image serving from database binary data via `/images/<artist_name>` route

## Development Commands

### Running the Application
```bash
# Development mode
python app.py

# Production mode (Heroku deployment)
gunicorn server:app --bind 0.0.0.0:$PORT
```

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Key dependencies: Flask, Bootstrap-Flask, SQLAlchemy, Selenium
```

### Environment Setup
- Create virtual environment: `python -m venv venv`
- Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
- Set `FLASK_SECRET_KEY` environment variable

## Data Management

### Web Scraping & Automation
- **Selenium automation** (`automation.py`): Chrome WebDriver class for web scraping
- **Data collection** (`db_games.py`): Downloads artist images and stores in database
- **Crawling scripts** (`crawling_scripts/`): Various data collection utilities

### File Processing
- **JSON data**: Music metadata stored in `jsons/` directory
- **Image storage**: Artist images stored as binary in database, served dynamically
- **CSV data**: Artist information in `artists.csv`

## Key Features

### Search Functionality
- Real-time autocomplete search via `/search` endpoint
- Searches both English and Greek song names
- Returns JSON results for frontend consumption

### Artist & Song Pages
- Dynamic routing: `/artist/<artist_name>` and `/song/<song_name>`
- Artist pages show all songs with media integration
- Song detail pages include video and demo content

### Image Management
- Images stored as binary data in SQLite
- Dynamic serving via Flask route with proper MIME types
- Automated image collection from web sources

## Important Notes

- Application loads all data into memory on startup for performance
- Greek and English text support throughout the application
- Heroku deployment ready with Procfile configuration
- Uses Bootstrap5 for responsive design
- No traditional build process - pure Python Flask application