from components.externalImports import *

db = SQLAlchemy()

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
