from flask import Flask, render_template, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my website password'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
app.config['SQLALCHEMY_BINDS'] = {"users": 'sqlite:///data.sqlite3', "photos": 'sqlite:///data.sqlite3'}
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'login'

#declaring user table in database
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    fname = db.Column(db.String(32))
    lname = db.Column(db.String(32))
    email = db.Column(db.String(300))
    username = db.Column(db.String(24))
    passwordHash = db.Column(db.String(128))
    galleries = db.relationship('Gallery', backref='user')

#declaring gallery table in database
class Gallery(db.Model):
    __tablename__ = 'galleries'
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey(User.id))
    numPhotos = db.Column(db.Integer)
    title = db.Column(db.String(40))
    dateCreated = db.Column(db.Date)
    dateLastEdited = db.Column(db.Date)
    description = db.Column(db.Text)
    photos = db.relationship('Photo', backref='gallery')

class Photo(db.Model):
    __tablename__ = 'photos'
    __bind_key__ = 'photos'
    id = db.Column(db.Integer, primary_key=True)
    galleryId = db.Column(db.Integer, db.ForeignKey(Gallery.id))
    photoURL = db.Column(db.String(32))
    thumbnailURL = db.Column(db.String(32))

    #hashes users password to add to database
    def set_password(self, password):
        self.passwordHash = generate_password_hash(password)

    #checks if entered password matches hashed one in database
    def verify_password(self, password):
        return check_password_hash(self.passwordHash, password)

    #used to add user to database
    @staticmethod
    def register(username, password, fname, lname, email):
        user = User(username=username, fname=fname, lname=lname, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def __repr__(self):
        return '<User {0}>'.format(self.username)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

#checks if current user is logged into website
def isLoggedIn():
    if 'loggedIn' not in session:
        session['loggedIn'] = False
        session.modified = True
    return session['loggedIn']

@app.route('/')
def homePage():
    galleries = Gallery.query.all()
    return render_template('index.html', galleries = galleries, loggedIn = isLoggedIn())

@app.route("/viewGallery<int:galleryID>")
def viewGallery(galleryID):
    #gets info for spefic gallery
    gallery = Gallery.query.filter_by("galleryId" == galleryID)
    photoURLs = []
    #adds all photo urls to a list
    for i in range(1, gallery.numPhotos + 1):
        photoPath = getattr(gallery, f'photoPath{i}')
        #included for robustness - shouldn't be needed if data correct
        if photoPath:
            photoURLs.append(photoPath)
    return render_template('indvGallery.html', title = gallery.title, description = gallery.description, numPhotos = gallery.numPhotos, dateCreated = gallery.dateCreated, dateLastEdited = gallery.dateLastEdited, photoURLS = photoURLs)


if __name__ == '__main__':
    app.run(debug=True)