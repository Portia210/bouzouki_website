import requests
import json
from flask import Flask, render_template, redirect, url_for, session, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
SEARCH_ENDPOINT = "https://api.themoviedb.org/3/search/movie"

headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzZWJjMGJmZWFmYTQ0NmMzMDdlODg1YTA5Yjg0MTU2MiIsInN1YiI6IjY2MTU2NzJiODcxYjM0MDE2MzFiNjM2YyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bDwDWnNvT8oO0tl4QvGc-GuXEhfIJT3e0DnfCxWNvOs"
}
parameters = {
    "include_adult": "true",
    "language": "en-US",
    "page": 1,
}

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///best-movies.db"
db = SQLAlchemy(app)


##CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[str] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=True)  # Allow null values
    rating: Mapped[str] = mapped_column(Float, nullable=True)  # Allow null values
    ranking: Mapped[str] = mapped_column(Integer, nullable=True)  # Allow null values
    review: Mapped[str] = mapped_column(String(250), nullable=True)  # Allow null values
    img_url: Mapped[str] = mapped_column(String(250), nullable=True)  # Allow null values

    # Optional: this will allow each movie object to be identified by its title when printed.
    def __repr__(self):
        return f'<Movie {self.title}>'


# Create table schema in the database. Requires application context.
with app.app_context():
    db.create_all()


class RateReviewForm(FlaskForm):
    rating_update = FloatField('Your Rating', validators=[DataRequired()])
    review_update = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


class NewMovieForm(FlaskForm):
    movie_name = StringField('Movie Name', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route("/")
def home():
    # Fetch all movies and sort them by rating
    movies = Movie.query.order_by(Movie.rating.desc()).all()

    # Update ranking based on sorted order
    for i, movie in enumerate(movies, start=1):
        movie.ranking = i

    # Commit the changes to the database
    db.session.commit()

    return render_template("index.html", all_movies=movies)


@app.route("/add", methods=['GET', 'POST'])
def add():
    form = NewMovieForm()
    if form.validate_on_submit():
        parameters["query"] = form.movie_name.data

        return redirect(url_for("select"))
    return render_template("add.html", form=form)


@app.route("/select")
def select():
    response = requests.get(SEARCH_ENDPOINT, headers=headers, params=parameters)
    movies_matches = response.json()["results"]
    return render_template("select.html", movies_matches=movies_matches)

@app.route("/add-movie/")
def add_movie():
    title = request.args.get('title')  # Get the serialized match object from the URL parameters
    img_url = f"https://image.tmdb.org/t/p/w185{request.args.get('img_url')}"  # Get the serialized match object from the URL parameters
    year = request.args.get('year').split("-")[0]  # Get the serialized match object from the URL parameters
    rating = request.args.get('rating') # Get the serialized match object from the URL parameters
    description = request.args.get('description')  # Get the serialized match object from the URL parameters
    rating = float(rating)
    rating = round(rating, 1)
    print(rating)
    with app.app_context():
        new_movie = Movie(title=title, img_url=img_url, year=year, description=description, rating=rating)
        db.session.add(new_movie)
        db.session.commit()
    return redirect(url_for("edit_movie", movie_title=title))


@app.route('/delete/<string:movie_title>', methods=['POST'])
def delete_movie(movie_title):
    with app.app_context():
        movie_to_delete = db.session.execute(db.select(Movie).where(Movie.title == movie_title)).scalar()
        # or book_to_delete = db.get_or_404(Book, book_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect("/")


@app.route('/edit/<string:movie_title>', methods=['GET', 'POST'])
def edit_movie(movie_title):
    form = RateReviewForm()
    if form.validate_on_submit():
        with app.app_context():
            movie_to_update = db.session.execute(db.select(Movie).where(Movie.title == movie_title)).scalar()
            movie_to_update.rating = form.rating_update.data
            movie_to_update.review = form.review_update.data
            db.session.commit()
        return redirect("/")
    return render_template('edit.html', form=form, movie_title=movie_title)


if __name__ == '__main__':
    app.run(debug=True)
