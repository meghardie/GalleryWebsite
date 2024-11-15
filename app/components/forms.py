from components.externalImports import *
from components.formValidators import *

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