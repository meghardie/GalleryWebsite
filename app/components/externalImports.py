# External imports
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