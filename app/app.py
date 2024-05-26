from flask import Flask, render_template, url_for, session, redirect, request
from flask_bootstrap import Bootstrap
from flask_session import Session
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, SubmitField, HiddenField, PasswordField, TextAreaField, MultipleFileField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO
from functools import wraps
import datetime, base64, json, os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my website password'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
app.config['SQLALCHEMY_BINDS'] = {"users": 'sqlite:///data.sqlite3', "photos": 'sqlite:///data.sqlite3'}
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = 'static/galleries'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  #16 MB

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
    email = db.Column(db.String(300), unique = True)
    username = db.Column(db.String(24))
    passwordHash = db.Column(db.String(128))
    galleries = db.relationship('Gallery', backref='user')

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

    @staticmethod
    def createGallery(userId, numPhotos, title, description):
        if userId != None:
            currentDate = datetime.date.today()
            gallery = Gallery(userId = userId, numPhotos = numPhotos, title = title, dateCreated = currentDate, dateLastEdited = currentDate, description = description)
            db.session.add(gallery)
            db.session.commit()
            return gallery
        return None

class Photo(db.Model):
    __tablename__ = 'photos'
    __bind_key__ = 'photos'
    id = db.Column(db.Integer, primary_key=True)
    galleryId = db.Column(db.Integer, db.ForeignKey(Gallery.id))
    photoURL = db.Column(db.String(32))
    thumbnailURL = db.Column(db.String(32))

    @staticmethod
    def addPhoto(galleryId, photoURL, thumbnailURL):
        photo = Photo(galleryId = galleryId, photoURL = photoURL, thumbnailURL = thumbnailURL)
        db.session.add(photo)
        db.session.commit()
        return photo

@lm.user_loader
def loadUser(id):
    return User.query.get(int(id))

def getCurrentUsername():
    currentUserID = session.get("userId", None)
    currentUsername = None
    if currentUserID != None:
        currentUsername = loadUser(currentUserID).username
    return currentUsername

def emailCheck(form, field):
    fdata = field.data
    if ('@' not in fdata) or ('.' not in fdata) or len(fdata) < 5:
        raise ValidationError("Please enter a valid email")

def containsData(form, field):
    if len(field.data) == 0:
        raise ValidationError("Please fill in this field")

def validPassword(form, field):
    fdata = field.data
    if len(fdata) < 6 or len(fdata) > 15:
        raise ValidationError("Password must be between 6 and 15 characters")
    if fdata.lower() == fdata:
        raise ValidationError("Password must contain at least 1 uppercase letter")

def passwordsMatch(form, field):
    if field.data != form.password1.data:
        raise ValidationError("Passwords do not match")

def updateEmailCheck(form, field):
    fdata = field.data
    if (('@' not in fdata) or ('.' not in fdata) or len(fdata) < 5) and len(fdata) != 0:
        raise ValidationError("Please enter a valid email")

def updatePasswordCheck(form, field):
    fdata = field.data
    if len(fdata) != 0:
        if fdata != form.password1.data:
            raise ValidationError("Passwords must match")
        if len(fdata) < 6 or len(fdata) > 15:
            raise ValidationError("Password must be between 6 and 15 characters")
        if fdata.lower() == fdata:
            raise ValidationError("Password must contain at least 1 uppercase letter")

#checks if current user is logged into website
def isLoggedIn():
    if 'loggedIn' not in session:
        session['loggedIn'] = False
        session.modified = True
    return session['loggedIn']

def getUsers(refresh = False):
    if (('users' not in globals())) or (refresh == True):
        result = User.query.all()
        global users
        users = {}
        for user in result:
            users[user.id] = {
                'id': user.id,
                'fname': user.fname,
                'lname': user.lname,
                'email': user.email,
                'username': user.username,
                'passwordHash': user.passwordHash,
                'galleries': [gallery.id for gallery in user.galleries]
            }
    return users

def getGalleries(refresh = False):
    if ('galleries' not in globals()) or (refresh == True):
        result = Gallery.query.all()
        global galleries 
        galleries = {}
        for gallery in result:
            galleries[gallery.id] = {
                'id': gallery.id,
                'userId': gallery.userId,
                'numPhotos': gallery.numPhotos,
                'title': gallery.title,
                'dateCreated': gallery.dateCreated,
                'dateLastEdited': gallery.dateLastEdited,
                'description': gallery.description,
                'photos': [photo.id for photo in gallery.photos]
            }
    return galleries

def getPhotos(refresh = False):
    if ('photos' not in globals()) or (refresh == True):
        result = Photo.query.all()
        global photos 
        photos = {}
        for photo in result:
            photos[photo.id] = {
                'id': photo.id,
                'galleryId': photo.galleryId,
                'photoURL': photo.photoURL,
                'thumbnailURL': photo.thumbnailURL
            }
    return photos

class loginForm(FlaskForm):
    email = StringField("Email: ", validators = [containsData, emailCheck])
    password = PasswordField("Password: ", validators = [containsData])
    submit = SubmitField('Submit')

class registerForm(FlaskForm):
    fname = StringField("First name(s): ", validators = [containsData])
    lname = StringField("Last name: ", validators = [containsData])
    email = StringField("Email: ", validators = [containsData, emailCheck])
    username = StringField("Username (this will be displayed to other users when you post a gallery): ", validators = [containsData])
    password1 = PasswordField("Password: ", validators = [containsData, validPassword])
    password2 = PasswordField("Confirm your password: ", validators = [containsData, passwordsMatch])
    submit = SubmitField("Create an account")

class settingsForm(FlaskForm):
    fname = StringField("First name:")
    lname = StringField("Last name: ")
    email = StringField("Email: ", validators = [updateEmailCheck])
    username = StringField("Username (this will be displayed to other users when you post a gallery): ")
    password1 = PasswordField("Change Password: ")
    password2 = PasswordField("Confirm your new password: ", validators = [updatePasswordCheck])
    submit = SubmitField("Update details")

class createGalleryForm(FlaskForm):
    title = StringField('Gallery Title: ', validators=[containsData, Length(max=100)])
    description = TextAreaField('Gallery Description: ', validators=[containsData])
    addPhoto = MultipleFileField()
    photos = HiddenField()
    submit = SubmitField("Create Gallery")

@app.route("/")
def homePage():
    return render_template('index.html', galleries = galleries, photos = photos, users = users, loggedIn = isLoggedIn(), username = getCurrentUsername())

@app.route("/viewGallery<int:galleryID>")
def viewGallery(galleryID):
    #gets info for spefic gallery
    gallery = getGalleries()[galleryID]
    photos = Photo.query.filter_by(galleryId=gallery['id']).all()
    URLs = {}
    count = 0
    #adds all photo urls to a list
    for photo in photos:
        URLs[count] = photo.photoURL
        count += 1
    print(URLs)
    return render_template('indvGallery.html', URLs = URLs, title = gallery['title'], description = gallery['description'], numPhotos = gallery['numPhotos'], dateCreated = gallery['dateCreated'], dateLastEdited = gallery['dateLastEdited'], username = users[gallery['userId']]["username"], loggedIn = isLoggedIn())

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = loginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is None or not user.verify_password(form.password.data):
            return render_template('login.html', loginAttempted = True, form = form, loggedIn = False)
        else:
            session['userId'] = user.id
            session['loggedIn'] = True
            session.modified = True
            return redirect(url_for('homePage'))
    return render_template('login.html', loginAttempted = False, form = form, loggedIn = isLoggedIn())

@app.route("/logout")
def logout():
    session.pop("userId")
    session['loggedIn'] = False
    session.modified = True
    return redirect(url_for('homePage'))

@app.route("/register", methods = ['GET', 'POST'])
def register():
    form = registerForm()
    if form.validate_on_submit():
        if User.query.filter_by(email = form.email.data).first() != None:
            return render_template('register.html', form = form, invalidEmail = True)
        else:
            newUser = User.register(form.username.data, form.password1.data, form.fname.data, form.lname.data, form.email.data)
            session['userId'] = newUser.id
            session['loggedIn'] = True
            session.modified = True
            global users
            users = getUsers(True)
            return redirect(url_for('homePage'))
    else:
        return render_template('register.html', form = form, invalidEmail = False)

@app.route("/addGallery", methods = ['GET', 'POST'])
def addGallery():
    form = createGalleryForm()
    if isLoggedIn():
        username = getCurrentUsername()
    else:
        username = None
    if form.validate_on_submit():
        print("valid form")
        title = form.title.data
        description = form.description.data
        photos = json.loads(form.photos.data)
        newGallery = Gallery.createGallery(session.get('userId'), len(photos), title, description)
        galleryId = newGallery.id
        for i in range (len(photos)):
            item = photos[i]
            filename = secure_filename(item['filename'])
            data = item['data']
            print(filename)
            if filename == '' or galleryId == '':
                return 'No selected file or gallery ID'
            
            if item:
                galleryFolder = (app.config['UPLOAD_FOLDER'] + "/" + str(galleryId))
                if not os.path.exists(galleryFolder):
                    os.makedirs(galleryFolder)
                filePath = galleryFolder + "/" + filename
    
                if ',' in data:
                    data= data.split(',')[1]
                
                data = base64.b64decode(data)
                image = Image.open(BytesIO(data))
                image.save(filePath)

                thumbnail = Image.open(filePath)
                thumbnailHeight = 125
                ratio = thumbnail.width / thumbnail.height
                newWidth = int(thumbnailHeight * ratio)
                thumbnail.thumbnail((newWidth, thumbnailHeight))
                fileExtension = os.path.splitext(filename)[1]
                thumbnailPath = (galleryFolder + "/" + "thumbnail" + str(i) + fileExtension)
                thumbnail.save(thumbnailPath)

                newPhoto = Photo.addPhoto(galleryId, filePath, thumbnailPath)
                
        photos = getPhotos(True)
        global galleries
        galleries = getGalleries(True)
        return redirect(url_for("homePage"))
    else:
        print("Invalid form")
        return render_template("addGallery.html", loggedIn = isLoggedIn(), form = form, currentDate = datetime.date.today(), username = username)

@app.route("/accountSettings", methods = ['GET', 'POST'])
def settings():
    form = settingsForm()
    if form.validate_on_submit():
        userId = session.get('userId')
        user = User.query.get(userId)
        if user:
            if len(form.fname.data) != 0:
                db.session.execute(update(User).where(User.id == userId).values(fname = form.fname.data))
                db.session.commit()
            if len(form.lname.data) != 0:
                db.session.execute(update(User).where(User.id == userId).values(lname = form.lname.data))
                db.session.commit()
            if len(form.email.data) != 0:
                db.session.execute(update(User).where(User.id == userId).values(email = form.email.data))
                db.session.commit()
            if len(form.username.data) != 0:
                db.session.execute(update(User).where(User.id == userId).values(username = form.username.data))
                db.session.commit()
            if len(form.password1.data) != 0:
                db.session.execute(update(User).where(User.id == userId).values(passwordHash = generate_password_hash(form.password1.data)))
                db.session.commit()
            global users
            users = getUsers(True)
            return redirect(url_for('homePage'))
    return render_template("settings.html", loggedIn = isLoggedIn(), form = form)

with app.app_context():
    users = getUsers()
    galleries = getGalleries()
    photos = getPhotos()

if __name__ == '__main__':
    app.run(debug=True)