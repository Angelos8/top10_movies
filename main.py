from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests as rq

TMBD_API = 'api key'


class RateMovieForm(FlaskForm):
    rating = StringField(label="Your rating out of 10:", validators=[DataRequired()])
    review = StringField(label="Your review:", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddMovieForm(FlaskForm):
    movie_title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'


# with app.app_context():
#     db.create_all()
#    new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()


@app.route("/")
def home():
    with app.app_context():
        movie_objects = Movie.query.order_by(Movie.rating).all()
        # each movie object has a ranking variable
        # the first movie on the list has the lowest rating so rank 10
        # the movie with the best rating has rank 1
        offset = 0
        for movie in movie_objects:
            movie.ranking = len(movie_objects) - offset
            offset += 1
    return render_template("index.html", movies=movie_objects)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    update_form = RateMovieForm()
    # get the movie_id with via a GET request
    received_id = request.args.get("movie_id")
    with app.app_context():
        movie = Movie.query.get(received_id)
        print(f'movie object {movie}')
        if request.method == 'POST':
            update_form.validate_on_submit()
            # receive data (it's returned in string type)
            new_rating = float(update_form.rating.data)
            new_review = update_form.review.data
            movie.rating = new_rating
            movie.review = new_review
            db.session.commit()
            return redirect(url_for('home'))
        return render_template('edit.html', form=update_form, title=movie.title, send_movie_id=received_id)


@app.route('/delete')
def delete_movie():
    received_id = request.args.get("movie_id")
    with app.app_context():
        movie = Movie.query.get(received_id)
        db.session.delete(movie)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add_movie():
    new_movie = AddMovieForm()
    if new_movie.validate_on_submit():
        search_title = new_movie.movie_title.data
        print(f'movie title entered by user: {search_title}')
        url = f'https://api.themoviedb.org/3/search/movie?api_key={TMBD_API}&query={search_title}'
        response = rq.get(url=url).json()
        # returns a list of dicts where each dict is data about a movie
        movie_list = response['results']
        for movie in movie_list:
            try:
                if movie['release_date'] != "":
                    temp = movie['release_date'].split('-')
                    date_string = f'{temp[2]}/{temp[1]}/{temp[0]}'
                    movie['release_date'] = date_string
            except:
                pass
        return render_template('select.html', movies=movie_list)
    return render_template('add.html', form=new_movie)


@app.route('/movie_data', methods=['GET', 'POST'])
def fetch_movie_data():
    movie_id = request.args.get("movie_id")
    response = rq.get(url=f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMBD_API}&language=en-US').json()
    # database columns
    poster_url = "https://image.tmdb.org/t/p/original" + response['poster_path']
    # create Movie object
    with app.app_context():
        try:
            new_movie = Movie(
                title=response['title'],
                year=int(response['release_date'].split('-')[0]),
                description=response['overview'],
                img_url=poster_url
            )
            db.session.add(new_movie)
            db.session.commit()
        except:
            return "<h1>Movie already exists! </h1>"
        # now I need to get the object from the database and pass the id
        # that's because the edit.html is coded to get data from the database
        movie = Movie.query.filter_by(title=response['title']).all()[0]
        return redirect(url_for('edit', title=movie.title, movie_id=movie.id))


if __name__ == '__main__':
    app.run(debug=True)
