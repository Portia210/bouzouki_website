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

with open("youtube_songs.json", "r") as json_file:
    imported_json = json.load(json_file)

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///best-movies.db"
# db = SQLAlchemy(app)
# #CREATE TABLE
# class song(db.Model):
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
#     description: Mapped[str] = mapped_column(String(250), nullable=True)
#     rating: Mapped[str] = mapped_column(Float, nullable=True)
#     ranking: Mapped[str] = mapped_column(Integer, nullable=True)
#     review: Mapped[str] = mapped_column(String(250), nullable=True)
#     img_url: Mapped[str] = mapped_column(String(250), nullable=True)

    # # Optional: this will allow each movie object to be identified by its title when printed.
    # def __repr__(self):
    #     return f'<Movie {self.title}>'


# Create table schema in the database. Requires application context.
# with app.app_context():
#     db.create_all()


# class RateReviewForm(FlaskForm):
#     rating_update = FloatField('Your Rating', validators=[DataRequired()])
#     review_update = StringField('Your Review', validators=[DataRequired()])
#     submit = SubmitField('Submit')
#


@app.route("/")
def home():
    # Fetch all movies and sort them by rating


    return render_template("index.html", all_movies=movies)




@app.route("/select")
def select():
    response = requests.get(SEARCH_ENDPOINT, headers=headers, params=parameters)
    movies_matches = response.json()["results"]
    return render_template("select.html", movies_matches=movies_matches)


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
