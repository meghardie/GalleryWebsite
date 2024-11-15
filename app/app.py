from components.imports import *

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
db.init_app(app)
lm = LoginManager(app)
lm.login_view = 'login'

#returns user in database from id
@lm.user_loader
def loadUser(id):
    return User.query.get(int(id))

@app.route("/")
def homePage():
    sortVar = request.args.get("sortGalls", "name")
    sortedGalls = galleries.copy()
    #sort galleries from newest to oldest
    if sortVar == "DateNtoO":
        sortedGalls = dict(sorted(sortedGalls.items(), key=lambda item: item[1]['dateCreated'], reverse = True))
    #sort galleries from oldest to newest
    elif sortVar == "DateOtoN":
        sortedGalls = dict(sorted(sortedGalls.items(), key=lambda item: item[1]['dateCreated']))
    #sort galleries by title A-Z
    elif sortVar == "AlphaAtoZ":
        sortedGalls = dict(sorted(sortedGalls.items(), key=lambda item: item[1]['title'].lower()))
    #sort galleries by title Z-A
    elif sortVar == "AlphaZtoA":
        sortedGalls = dict(sorted(sortedGalls.items(), key=lambda item: item[1]['title'].lower(), reverse = True))
    #sort galleries by username A-Z
    elif sortVar == "username":
        sortedGalls = dict(sorted(sortedGalls.items(), key=lambda item: users[item[1]['userId']]['username']))
    #if sortVar undefined then sort by date - newest to oldest
    else:
        sortedGalls = dict(sorted(sortedGalls.items(), key=lambda item: item[1]['dateCreated'], reverse= True))
    return render_template('index.html', galleries = sortedGalls, photos = photos, users = users, loggedIn = isLoggedIn(), username = getCurrentUsername())

@app.route("/viewGallery<int:galleryID>")
def viewGallery(galleryID):
    #gets info for spefic gallery and its photos
    gallery = getGalleries(Gallery)[galleryID]
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
    #checks that user logged in owns gallery
    ownerID = Gallery.query.filter_by(id = galleryID).first().userId
    currentUserID = session.get('userId')
    #if they don't own they are redirected to another webpage
    if (ownerID != currentUserID):
        return redirect(url_for("accessDenied"))
    
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
        newPhotos = json.loads(form.photos.data)
        #update dateLastEdited
        db.session.execute(update(Gallery).where(Gallery.id == galleryID).values(dateLastEdited = datetime.date.today()))
        db.session.commit()
        #if title has been changed it is updated
        if newTitle != gallery.title:
            db.session.execute(update(Gallery).where(Gallery.id == galleryID).values(title = newTitle))
            db.session.commit()
        #if description has been changed it is updated
        if newDesc != gallery.description:
            db.session.execute(update(Gallery).where(Gallery.id == galleryID).values(description = newDesc))
            db.session.commit()
        
        #save any kept data
        for i in range (len(newPhotos)):
            photo = newPhotos[i]
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
        for i in range (len(newPhotos)):
            photo = newPhotos[i]
            filePath, thumbnailPath = savePhoto(photo['data'], galleryFolder, os.path.basename(photo['filename']), i)
            Photo.addPhoto(galleryID, filePath, thumbnailPath)

        #update numPhotos in database
        db.session.execute(update(Gallery).where(Gallery.id==galleryID).values(numPhotos = len(newPhotos)))
        db.session.commit()

        #updates dictionaries containing database info
        global photos
        photos = getPhotos(Photo, True)
        global galleries
        galleries = getGalleries(Gallery, True)
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
            users = getUsers(User, True)
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
        gallPhotos = json.loads(form.photos.data)
        #adds gallery to database
        newGallery = Gallery.createGallery(session.get('userId'), len(gallPhotos), title, description)
        galleryId = newGallery.id
        #adds each photo to database and server
        for i in range (len(gallPhotos)):
            #gets info about photo
            item = gallPhotos[i]
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
        global photos
        photos = getPhotos(Photo, True)
        global galleries
        galleries = getGalleries(Gallery, True)
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
            users = getUsers(User, True)
            return redirect(url_for('homePage'))
    return render_template("settings.html", loggedIn = loggedIn, form = form,  username = getCurrentUsername())

@app.route("/accessDenied")
def accessDenied():
    return render_template("accessDenied.html")

#sets up the initial database dictionaries
with app.app_context():
    users = getUsers(User)
    galleries = getGalleries(Gallery)
    photos = getPhotos(Photo)

if __name__ == '__main__':
    app.run(debug=True)