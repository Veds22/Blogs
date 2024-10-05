from datetime import date
from functools import wraps
import os
import flask_bootstrap
from flask import Flask, render_template, redirect, url_for, request, flash, abort, session
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, Post

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
ckeditor = CKEditor(app)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
flask_bootstrap.Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)

# CREATE DATABASE

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "DATABASE_URI")
db = SQLAlchemy(model_class=Base)
db.init_app(app)
print(os.getenv('FLASK_KEY'), os.getenv('DATABASE_URI'))

def admin_only(wrapper_function):
    @wraps(wrapper_function)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return wrapper_function(*args, **kwargs)

    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CONFIGURE TABLE


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.user_id"))
    author: Mapped["User"] = relationship("User", back_populates="posts")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    posts: Mapped[list["BlogPost"]] = relationship("BlogPost", back_populates="author")

    def get_id(self):
        return str(self.user_id)


with app.app_context():
    db.create_all()


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit() and request.method == "POST":
        try:
            new_user = User(
                email=request.form.get('email'),
                name=request.form.get('name'),
                password=generate_password_hash(
                    request.form.get('password'),
                    method="pbkdf2:sha256",
                    salt_length=8
                )
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
        except:
            flash("You've already signed up with that email.\nLog-in instead.")
            return redirect(url_for("login"))
    return render_template("register.html", form=form, year=date.today().year)


@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if request.method == "POST":
        email = login_form.email.data
        password = login_form.password.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user:
            flash("User does not exist. Register first")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Bad Credentials")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=login_form, year=date.today().year)


@app.route("/")
@app.route('/all-posts')
def get_all_posts():
    post_list = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", user=current_user, all_posts=post_list, year=date.today().year)


@login_required
@app.route('/post', methods=["GET"])
def show_post():
    post_id = request.args.get("post_id")
    requested_post = db.get_or_404(BlogPost, post_id)
    print(requested_post.author_id, current_user.user_id)
    return render_template("post.html", post=requested_post, user=current_user, year=date.today().year)


@login_required
@admin_only
@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = Post()
    if request.method == "POST" and form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            author=current_user,
            img_url=form.img_url.data,
            body=form.body.data,
            date=date.today().strftime("%B %d, %Y")
        )
        with app.app_context():
            db.session.add(new_post)
            db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, year=date.today().year)


@login_required
@admin_only
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    form = Post(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if request.method == "POST" and form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.img_url = form.img_url.data
        post.body = form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post_id))
    return render_template("make-post.html", form=form, year=date.today().year)


@login_required
@admin_only
@app.route("/delete/<post_id>")
def delete_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("get_all_posts"))


@app.route("/about")
def about():
    return render_template("about.html", year=date.today().year)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('get_all_posts'))


@app.route("/contact")
def contact():
    return render_template("contact.html", year=date.today().year)


if __name__ == "__main__":
    app.run(debug=False, port=5003)
