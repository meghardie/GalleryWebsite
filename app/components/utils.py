from components.externalImports import *
from app import loadUser

#returns the username from user in current session, or None if not logged in
def getCurrentUsername():
    currentUserID = session.get("userId", None)
    currentUsername = None
    if currentUserID != None:
        currentUsername = loadUser(currentUserID).username
    return currentUsername

#checks if current user is logged into website
def isLoggedIn():
    if 'loggedIn' not in session:
        session['loggedIn'] = False
        session.modified = True
    return session['loggedIn']

#saves an image to the server and the database
#takes photos data, folder to be stored in and filename
def savePhoto(data, galleryFolder, filename, photoNum):
    filePath = galleryFolder + "/" + filename
    print("Saving photo... file path = " + filePath)
    if ',' in data:
        data= data.split(',')[1]

    data = base64.b64decode(data)
    #save full image
    image = Image.open(BytesIO(data))
    image.save(filePath)

    #calculate thumbnail dimensions
    thumbnail = Image.open(filePath)
    maxThumbHeight = 125
    maxThumbWidth = 125
    width = thumbnail.width
    height = thumbnail.height
    ratio = width / height
    #crop thumbnail to right size
    #if photo is wider than tall then max width = 125px
    if ratio > 1:
        height = maxThumbHeight
        width = int(height * ratio)
    #if photo is taller than wide max height = 125px
    else:
        width = maxThumbWidth
        height = int(width / ratio)
    thumbnail.thumbnail((width, height))

    #crop thumbnail to exact size
    centerWidth = width//2
    centerHeight = height//2
    left = centerWidth - (maxThumbWidth//2)
    right = centerWidth + (maxThumbWidth//2)
    top = centerHeight - (maxThumbHeight//2)
    bottom = centerHeight + (maxThumbHeight//2)
    print(width)
    print(height)
    print(centerWidth)
    print(centerHeight)
    print(left)
    print(centerWidth)
    print(right)
    print(top)
    print(bottom)

    thumbnail = thumbnail.crop((left, top, right, bottom))

    fileExtension = os.path.splitext(filename)[1]
    thumbnailPath = (galleryFolder + "/" + "thumbnail" + str(photoNum) + fileExtension)
    thumbnail.save(thumbnailPath)

    return filePath, thumbnailPath