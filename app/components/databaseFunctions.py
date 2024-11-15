from components.externalImports import *

#gets the current dictionary containing all users in database
#refresh means will refetch info from the database
def getUsers(User, refresh = False):
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
def getGalleries(Gallery, refresh = False):
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
def getPhotos(Photo, refresh = False):
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