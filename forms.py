from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import  CKEditorField

class Post(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Image  URL", validators=[URL()])
    body = CKEditorField("Body", validators=[DataRequired()])
    submit = SubmitField("Post it")


class RegisterForm(FlaskForm):
    email = StringField("E-Mail", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("SIGN ME UP!")


class LoginForm(FlaskForm):
    email = StringField("E-Mail", validators=[DataRequired(), URL()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login!")
    
    