from components.externalImports import *

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