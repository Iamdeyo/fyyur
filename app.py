#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

# import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
from config import SQLALCHEMY_DATABASE_URI
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
  __tablename__ = 'venues'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  address = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500), nullable=False)
  facebook_link = db.Column(db.String(120), nullable=False)
  website = db.Column(db.String(120), nullable=False)
  seeking_talent = db.Column(db.Boolean(), default=False)
  seeking_description = db.Column(db.String(500), nullable=False)
  genres = db.Column(db.String(120), nullable=False)
  shows = db.relationship('Show', backref='venues', lazy=True)

  def __repr__(self):
    return f'<{self.name}, {self.city}, {self.phone}>'

class Artist(db.Model):
  __tablename__ = 'artists'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  genres = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500), nullable=False)
  facebook_link = db.Column(db.String(120), nullable=False)
  website_link = db.Column(db.String(120), nullable=False)
  seeking_venue = db.Column(db.Boolean(), default=False)
  seeking_description = db.Column(db.String(500), nullable=False)
  shows = db.relationship('Show', backref='artists', lazy=True)

  def __repr__(self):
    return f'<{self.name}, {self.city}, {self.phone}>'

class Show(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
  start_time = db.Column(db.DateTime, default=datetime.utcnow)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  city = ''
  state = ''
  city_state = []
  venue = []
  upcoming_shows = []
  venueData = []
  data = []
  
  venues = Venue.query.all()
  # looping through datas from the venues to add the upcoming show count
  for v in venues:
      shows = Show.query.filter_by(venue_id=v.id).all()
      for show in shows:
        # check for upcoimg shows
        if datetime.now() < show.start_time:
          upcoming_shows.append(show)
      v.__dict__['num_upcoming_shows'] = len(upcoming_shows)
      venueData.append(v.__dict__)

  # looping through the new venues data to groups by city and state.
  for venue in venueData:
    cityState = venue['city'] + ',' + venue['state']
    if cityState in city_state:
      None
    else:
      city_state.append(cityState)

  # getting the venue by city and state
  for cs in city_state:
    cs = cs.split(',')
    city = cs[0]
    state = cs[1]  
    venue = Venue.query.filter_by(city=city, state=state).all()
  
    data.append({
      "city": city,
      "state": state,
      "venues": venue
    })
    
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # getting the searched term from the form
  searched_word= request.form['search_term']

  # Implementing a Search Venues by name, City or State.
  data = Venue.query.filter(Venue.name.ilike('%' + searched_word + '%') | Venue.city.ilike('%' + searched_word + '%') | Venue.state.ilike('%' + searched_word + '%')).all()

  response={
    "count": len(data),
    "data": data
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  data = Venue.query.filter_by(id=venue_id).one()
  # converting the data to a dictionary
  data = data.__dict__
  past_shows= []
  upcoming_shows= []
  shows = Show.query.filter_by(venue_id=venue_id).all()

  for show in shows:
    artist = Artist.query.get(show.artist_id)
    # converting the data from show to a dictionary
    show = show.__dict__
    show['artist_name'] = artist.name
    show['artist_image_link'] = artist.image_link

    # check for past or upcoimg shows
    if datetime.now() >= show['start_time']:
      show['start_time'] = show['start_time'].strftime("%Y-%m-%dT%H:%M:%SZ")
      past_shows.append(show)
    else:
      show['start_time'] = show['start_time'].strftime("%Y-%m-%dT%H:%M:%SZ")
      upcoming_shows.append(show)
      
  data['past_shows']= past_shows
  data['upcoming_shows']= upcoming_shows
  data['past_shows_count']= len(past_shows)
  data['upcoming_shows_count']= len(upcoming_shows)

  # converting the string data to a list
  genre_list = data['genres'].replace('{', ',').replace('}', ',').split(',')
  genre_list.pop()
  genre_list.pop(0)
  data['genres'] = genre_list
  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    form = VenueForm()
    venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data, phone=form.phone.data, image_link=form.image_link.data, facebook_link=form.facebook_link.data, website=form.website_link.data, seeking_talent=form.seeking_talent.data, seeking_description=form.seeking_description.data, genres=form.genres.data)

    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  return redirect(url_for('index'))

@app.route('/venues/<venue_id>/delete')
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()       
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # getting the searched term from the form
  searched_word= request.form['search_term']

  # Implementing a Search Venues by name, City or State.
  data = Artist.query.filter(Artist.name.ilike('%' + searched_word + '%') | Artist.city.ilike('%' + searched_word + '%') | Artist.state.ilike('%' + searched_word + '%')).all()

  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  data = Artist.query.filter_by(id=artist_id).one()
  # converting data to a dictionary
  data = data.__dict__
  past_shows= []
  upcoming_shows= []
  shows = Show.query.filter_by(artist_id=artist_id).all()

  for show in shows:
    venue = Venue.query.get(show.venue_id)
    # converting the data from show to a dictionary
    show = show.__dict__
    show['venue_name'] = venue.name
    show['venue_image_link'] = venue.image_link
    # check for past or upcoimg shows
    if datetime.now() >= show['start_time']:
      show['start_time'] = show['start_time'].strftime("%Y-%m-%dT%H:%M:%SZ")
      past_shows.append(show)
    else:
      show['start_time'] = show['start_time'].strftime("%Y-%m-%dT%H:%M:%SZ")
      upcoming_shows.append(show)

  data['past_shows']= past_shows
  data['upcoming_shows']= upcoming_shows
  data['past_shows_count']= len(past_shows)
  data['upcoming_shows_count']= len(upcoming_shows)
  # converting the string data to a list
  genre_list = data['genres'].replace('{', ',').replace('}', ',').split(',')
  genre_list.pop()
  genre_list.pop(0)
  data['genres'] = genre_list
 
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist= Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    form = ArtistForm()
    venue = Artist.query.get(artist_id)
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.genres = form.genres.data
    venue.facebook_link = form.facebook_link.data
    venue.image_link = form.image_link.data
    venue.website_link = form.website_link.data
    venue.seeking_venue = form.seeking_venue.data
    venue.seeking_description = form.seeking_description.data

    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).one()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  try:
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.genres = form.genres.data
    venue.facebook_link = form.facebook_link.data
    venue.image_link = form.image_link.data
    venue.website_link = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data

    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    form = ArtistForm()
    artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data, genres=form.genres.data, image_link=form.image_link.data, facebook_link=form.facebook_link.data, website_link=form.website_link.data, seeking_venue=form.seeking_venue.data, seeking_description=form.seeking_description.data, )
    
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  
  return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data=[]
  shows = Show.query.all()

  for show in shows:
    venue = Venue.query.get(show.venue_id)
    artist = Artist.query.get(show.artist_id)
    # converting the data from show to a dictionary
    show = show.__dict__
    show['venue_name'] = venue.name
    show['artist_name'] = artist.name
    show['artist_image_link'] = artist.image_link
    show['start_time'] = show['start_time'].strftime("%Y-%m-%dT%H:%M:%SZ")
    data.append(show)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    form = ShowForm()
    venue = Venue.query.filter_by(id=form.venue_id.data).all()
    artist = Artist.query.filter_by(id=form.artist_id.data).all()
    # check if Artist ID and Venue ID exist
    if venue and artist:
      show = Show(artist_id=form.artist_id.data, venue_id=form.venue_id.data, start_time=form.start_time.data )
      db.session.add(show)
      db.session.commit()
    else:
     flash('An error occurred. Show could not be listed.')
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
    if error:
     flash('An error occurred. Show could not be listed.')
    else:
      # on successful db insert, flash success
     flash('Show was successfully listed!')
  return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
