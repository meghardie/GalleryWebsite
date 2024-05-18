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
app.config['SQLALCHEMY_BINDS'] = {"users": 'sqlite:///data.sqlite3'}
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'login'


class Gallery(db.Model):
    __tablename__ = 'galleries'
    galleryId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer)
    numPhotos = db.Column(db.Integer)
    title = db.Column(db.String(40))
    dateCreated = db.Column(db.Date)
    dateLastEdited = db.Column(db.Date)
    description = db.Column(db.Text)
    photoPath1 = db.Column(db.String(30))
    photoPath2 = db.Column(db.String(30))
    photoPath3 = db.Column(db.String(30))
    photoPath4 = db.Column(db.String(30))
    photoPath5 = db.Column(db.String(30))
    photoPath6 = db.Column(db.String(30))
    photoPath7 = db.Column(db.String(30))
    photoPath8 = db.Column(db.String(30))
    photoPath9 = db.Column(db.String(30))
    photoPath10 = db.Column(db.String(30))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __bind_key__ = 'users'
    userId = db.Column(db.Integer, primary_key = True)
    fname = db.Column(db.String(32))
    lname = db.Column(db.String(32))
    email = db.Column(db.String(300))
    username = db.Column(db.String(24))
    passwordHash = db.Column(db.String(128))

    def set_password(self, password):
        self.passwordHash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.passwordHash, password)

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

@app.route('/')
def homePage():
    return render_template('index.html', loggedIn = False)


if __name__ == '__main__':
    app.run(debug=True)