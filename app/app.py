from flask import Flask, render_template, url_for, session, redirect, request
from flask_bootstrap import Bootstrap
from flask_session import Session
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, SubmitField, HiddenField, PasswordField, TextAreaField, MultipleFileField
from wtforms.validators import ValidationError, Length
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update, delete
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO
from functools import wraps
import datetime, base64, json, os

#setting up app
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

    #used to add photo to the database
    @staticmethod
    def createGallery(userId, numPhotos, title, description):
        if userId != None:
            currentDate = datetime.date.today()
            gallery = Gallery(userId = userId, numPhotos = numPhotos, title = title, dateCreated = currentDate, dateLastEdited = currentDate, description = description)
            db.session.add(gallery)
            db.session.commit()
            return gallery
        return None

#declaring photo table in database
class Photo(db.Model):
    __tablename__ = 'photos'
    __bind_key__ = 'photos'
    id = db.Column(db.Integer, primary_key=True)
    galleryId = db.Column(db.Integer, db.ForeignKey(Gallery.id))
    photoURL = db.Column(db.String(32))
    thumbnailURL = db.Column(db.String(32))

    #used to add photo to the database
    @staticmethod
    def addPhoto(galleryId, photoURL, thumbnailURL):
        photo = Photo(galleryId = galleryId, photoURL = photoURL, thumbnailURL = thumbnailURL)
        db.session.add(photo)
        db.session.commit()
        print("Added photo")
        return photo

#returns user in database from id
@lm.user_loader
def loadUser(id):
    return User.query.get(int(id))

#returns the username from user in current session, or None if not logged in
def getCurrentUsername():
    currentUserID = session.get("userId", None)
    currentUsername = None
    if currentUserID != None:
        currentUsername = loadUser(currentUserID).username
    return currentUsername

#checks if email entered in form is valid
def emailCheck(form, field):
    fdata = field.data
    #must contains an '@' a '.' and be more than 5 characters
    if ('@' not in fdata) or ('.' not in fdata) or len(fdata) < 5:
        raise ValidationError("Please enter a valid email")

#checks if a form field recieved contains any data
def containsData(form, field):
    if len(field.data) == 0:
        raise ValidationError("Please fill in this field")

#checks if a password entered in a form passes security checks
def validPassword(form, field):
    fdata = field.data
    #password must be between 6 and 15 characters and contain at least 1 uppercase letter
    if len(fdata) < 6 or len(fdata) > 15:
        raise ValidationError("Password must be between 6 and 15 characters")
    if fdata.lower() == fdata:
        raise ValidationError("Password must contain at least 1 uppercase letter")

#checks if passwords sent in form for changing passwords match
def passwordsMatch(form, field):
    if field.data != form.password1.data:
        raise ValidationError("Passwords do not match")

#checks if new email to be changed is valid
def updateEmailCheck(form, field):
    fdata = field.data
    #must contains an '@' a '.' and be more than 5 characters
    if (('@' not in fdata) or ('.' not in fdata) or len(fdata) < 5) and len(fdata) != 0:
        raise ValidationError("Please enter a valid email")

#checks if new password to be changed passes security checks
def updatePasswordCheck(form, field):
    fdata = field.data
    if len(fdata) != 0:
        validPassword(form, field)

#checks if current user is logged into website
def isLoggedIn():
    if 'loggedIn' not in session:
        session['loggedIn'] = False
        session.modified = True
    return session['loggedIn']

#gets the current dictionary containing all users in database
#refresh means will refetch info from the database
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

#gets the current dictionary containing all galleries in database
#refresh means will refetch info from the database
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

#gets the current dictionary containing all photos in database
#refresh means will refetch info from the database
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

#saves an image to the server and the database
#takes photos data, folder to be stored in and filename
def savePhoto(data, galleryFolder, filename, photoNum):
    filePath = galleryFolder + "/" + filename
    print("Saving photo... file path = " + filePath)
    if ',' in data:
        data= data.split(',')[1]

    data = base64.b64decode(data)
    
    image = Image.open(BytesIO(data))
    image.save(filePath)

    thumbnail = Image.open(filePath)
    maxThumbHeight = 125
    maxThumbWidth = 125
    width = thumbnail.width
    height = thumbnail.height
    ratio = width / height

    #if photo is wider than tall then max width = 125px
    if ratio > 1:
        width = maxThumbWidth
        height = int(width / ratio)
    #if photo is taller than wide max height = 125px
    else:
        height = maxThumbHeight
        width = int(height * ratio)

    # newWidth = int(thumbnailHeight * ratio)
    thumbnail.thumbnail((width, height))
    fileExtension = os.path.splitext(filename)[1]
    thumbnailPath = (galleryFolder + "/" + "thumbnail" + str(photoNum) + fileExtension)
    thumbnail.save(thumbnailPath)

    return filePath, thumbnailPath

#form to login to account
class loginForm(FlaskForm):
    email = StringField("Email: ", validators = [containsData, emailCheck])
    password = PasswordField("Password: ", validators = [containsData])
    submit = SubmitField('Submit')

#form to create an account
class registerForm(FlaskForm):
    fname = StringField("First name(s): ", validators = [containsData])
    lname = StringField("Last name: ", validators = [containsData])
    email = StringField("Email: ", validators = [containsData, emailCheck])
    username = StringField("Username (this will be displayed to other users when you post a gallery): ", validators = [containsData])
    password1 = PasswordField("Password: ", validators = [containsData, validPassword])
    password2 = PasswordField("Confirm your password: ", validators = [containsData, passwordsMatch])
    submit = SubmitField("Create an account")

#form to change any of your user info in the database
class settingsForm(FlaskForm):
    fname = StringField("First name:")
    lname = StringField("Last name: ")
    email = StringField("Email: ", validators = [updateEmailCheck])
    username = StringField("Username (this will be displayed to other users when you post a gallery): ")
    password1 = PasswordField("Change Password: ")
    password2 = PasswordField("Confirm your new password: ", validators = [updatePasswordCheck])
    submit = SubmitField("Update details")

#form to create or change info for a gallery
class createGalleryForm(FlaskForm):
    title = StringField('Gallery Title: ', validators=[containsData, Length(max=100)])
    description = TextAreaField('Gallery Description: ', validators=[containsData])
    addPhoto = MultipleFileField()
    photos = HiddenField()
    submit = SubmitField("")

@app.route("/")
def homePage():
    return render_template('index.html', galleries = galleries, photos = photos, users = users, loggedIn = isLoggedIn(), username = getCurrentUsername())

@app.route("/viewGallery<int:galleryID>")
def viewGallery(galleryID):
    #gets info for spefic gallery and its photos
    gallery = getGalleries()[galleryID]
    photos = Photo.query.filter_by(galleryId=gallery['id']).all()
    URLs = {}
    count = 0
    #adds all photo urls to a list
    for photo in photos:
        URLs[count] = photo.photoURL
        count += 1
    return render_template('indvGallery.html', URLs = URLs, username = getCurrentUsername(), title = gallery['title'], description = gallery['description'], numPhotos = gallery['numPhotos'], dateCreated = gallery['dateCreated'], dateLastEdited = gallery['dateLastEdited'], galleryUsername = users[gallery['userId']]["username"], loggedIn = isLoggedIn())

@app.route("/editGallery<int:galleryID>", methods = ['GET', 'POST'])
def editGallery(galleryID):
    #gets info about relevant gallery and its photos
    gallery = Gallery.query.filter_by(id = galleryID).first()
    oldPhotos = Photo.query.filter_by(galleryId=gallery.id).all()
    oldURLs = {}
    count = 0
    #adds all photo urls to a list
    for photo in oldPhotos:
        oldURLs[count] = photo.photoURL
        count += 1
    form = createGalleryForm()

    if form.validate_on_submit():
        #sets folder for photos to be saved to on the server
        galleryFolder = (app.config['UPLOAD_FOLDER'] + "/" + str(galleryID))
        #gets latest gallery info from form
        newTitle = form.title.data
        newDesc = form.description.data
        photos = json.loads(form.photos.data)
        #if title has been changed it is updated
        if newTitle != gallery.title:
            db.session.execute(update(Gallery).where(Gallery.id == galleryID).values(title = newTitle))
            db.session.commit()
        #if description has been changed it is updated
        if newDesc != gallery.description:
            db.session.execute(update(Gallery).where(Gallery.id == galleryID).values(description = newDesc))
            db.session.commit()
        
        #save any kept data
        for i in range (len(photos)):
            photo = photos[i]
            if photo['original'] == True:
                filePath = photo['filename']
                print("File path = " + filePath)
                img = Image.open(filePath)
                data = BytesIO()
                img.save(data, format=img.format)
                data.seek(0)
                photoData = base64.b64encode(data.getvalue()).decode('utf-8')
                photo['data'] = photoData
        
        #delete existing photos from database
        db.session.execute(delete(Photo).where(Photo.galleryId == galleryID))
        db.session.commit()

        #save new photos to server and database
        for i in range (len(photos)):
            photo = photos[i]
            filePath, thumbnailPath = savePhoto(photo['data'], galleryFolder, os.path.basename(photo['filename']), i)
            Photo.addPhoto(galleryID, filePath, thumbnailPath)

        #update numPhotos in database
        db.session.execute(update(Gallery).where(Gallery.id==galleryID).values(numPhotos = len(photos)))
        db.session.commit()

        #updates dictionaries containing database info
        photos = getPhotos(True)
        global galleries
        galleries = getGalleries(True)
        return redirect(url_for("homePage"))
    
    form.title.data = gallery.title
    form.description.data = gallery.description
    return render_template('editGallery.html', form = form, currentDate = datetime.date.today(), dateCreated = gallery.dateCreated, URLs = oldURLs, firstPhoto = oldURLs[0])

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = loginForm()
    if form.validate_on_submit():
        #checks if user account exists
        user = User.query.filter_by(email = form.email.data.lower()).first()
        #returns error message if account doesn't exist or password is wrong
        if user is None or not user.verify_password(form.password.data):
            return render_template('login.html', loginAttempted = True, form = form, loggedIn = False)
        else:
            #if login right sets session info for that user and sends them to the homepage 
            session['userId'] = user.id
            session['loggedIn'] = True
            session.modified = True
            return redirect(url_for('homePage'))
    return render_template('login.html', loginAttempted = False, form = form, loggedIn = isLoggedIn(),  username = getCurrentUsername())

@app.route("/logout")
def logout():
    #removes user info from session to 'log them out'
    session.pop("userId")
    session['loggedIn'] = False
    session.modified = True
    return redirect(url_for('homePage'))

@app.route("/register", methods = ['GET', 'POST'])
def register():
    form = registerForm()
    if form.validate_on_submit():
        #checks if there is already an account with that email
        if User.query.filter_by(email = form.email.data).first() != None:
            #if account already exists send error
            return render_template('register.html', form = form, invalidEmail = True)
        else:
            #adds new user to database
            newUser = User.register(form.username.data, form.password1.data, form.fname.data, form.lname.data, form.email.data)
            #logs user in to session
            session['userId'] = newUser.id
            session['loggedIn'] = True
            session.modified = True
            #updates users dictionary
            global users
            users = getUsers(True)
            return redirect(url_for('homePage'))
    else:
        return render_template('register.html', form = form, invalidEmail = False)

@app.route("/addGallery", methods = ['GET', 'POST'])
def addGallery():
    #checks if user is logged in, if not they are redirected to different page
    loggedIn = isLoggedIn()
    if not loggedIn:
        return render_template('loginNeeded.html', loggedIn = loggedIn)
    
    form = createGalleryForm()
    username = getCurrentUsername()

    if form.validate_on_submit():
        #gets gallery details from form
        title = form.title.data
        description = form.description.data
        photos = json.loads(form.photos.data)
        #adds gallery to database
        newGallery = Gallery.createGallery(session.get('userId'), len(photos), title, description)
        galleryId = newGallery.id
        #adds each photo to database and server
        for i in range (len(photos)):
            #gets info about photo
            item = photos[i]
            filename = secure_filename(item['filename'])
            data = item['data']
            if filename == '' or galleryId == '':
                return 'No selected file or gallery ID'
            
            if item:
                #create gallery folder
                galleryFolder = (app.config['UPLOAD_FOLDER'] + "/" + str(galleryId))
                if not os.path.exists(galleryFolder):
                    os.makedirs(galleryFolder)
                
                #save to server
                filePath, thumbnailPath = savePhoto(data, galleryFolder, filename, i)
                #add to database
                newPhoto = Photo.addPhoto(galleryId, filePath, thumbnailPath)
                
        #updates info in database dictionaries
        photos = getPhotos(True)
        global galleries
        galleries = getGalleries(True)
        return redirect(url_for("homePage"))
    else:
        return render_template("addGallery.html", loggedIn = loggedIn, form = form, currentDate = datetime.date.today(), username = username)

@app.route("/myGalleries")
def myGalleries():
    myGalls = []
    #checks if logged in, if not redirected
    loggedIn = isLoggedIn()
    if not loggedIn:
        return render_template('loginNeeded.html', loggedIn = loggedIn)
    
    #gets relevant galleries
    myGalls = Gallery.query.filter_by(userId=session['userId']).all()
    return render_template('myGalleries.html', loggedIn = loggedIn, photos = photos, galleries = myGalls, username = getCurrentUsername(), users = users)

@app.route("/accountSettings", methods = ['GET', 'POST'])
def settings():
    #checks if logged in, if not redirected
    loggedIn = isLoggedIn()
    if not loggedIn:
        return render_template('loginNeeded.html', loggedIn = loggedIn)
    
    form = settingsForm()
    if form.validate_on_submit():
        #gets current user details
        userId = session.get('userId')
        user = User.query.get(userId)
        if user:
            #if something has been changed it is updated in the database
            if len(form.fname.data) != 0:
                db.session.execute(update(User).where(User.id == userId).values(fname = form.fname.data))
                db.session.commit()
            if len(form.lname.data) != 0:
                db.session.execute(update(User).where(User.id == userId).values(lname = form.lname.data))
                db.session.commit()
            if len(form.email.data) != 0:
                db.session.execute(update(User).where(User.id == userId).values(email = form.email.data.lower()))
                db.session.commit()
            if len(form.username.data) != 0:
                db.session.execute(update(User).where(User.id == userId).values(username = form.username.data))
                db.session.commit()
            if len(form.password1.data) != 0:
                db.session.execute(update(User).where(User.id == userId).values(passwordHash = generate_password_hash(form.password1.data)))
                db.session.commit()
            #updates user dictionary as databse has been changed
            global users
            users = getUsers(True)
            return redirect(url_for('homePage'))
    return render_template("settings.html", loggedIn = loggedIn, form = form,  username = getCurrentUsername())

#sets up the initial database dictionaries
with app.app_context():
    users = getUsers()
    galleries = getGalleries()
    photos = getPhotos()

if __name__ == '__main__':
    app.run(debug=True)