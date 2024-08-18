from flask import Flask, flash, render_template, request,url_for,redirect
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField,BooleanField,ValidationError
from wtforms.validators import DataRequired,EqualTo,length
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime,date
from wtforms.widgets import TextArea

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config['SECRET_KEY'] = "pesbd101518"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Posts(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     title=db.Column(db.String(255))
     content=db.Column(db.Text)
     author=db.Column(db.String(255))
     date_posted=db.Column(db.DateTime, default=datetime.utcnow)
     slug=db.Column(db.String(255))


class PostForm(FlaskForm):
    title=StringField("Title",validators=[DataRequired()])
    content=StringField("Content",validators=[DataRequired()], widget=TextArea())
    author=StringField("Author",validators=[DataRequired()])
    slug=StringField("Slug",validators=[DataRequired()])
    submit=SubmitField("Submit")


# Create model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    favorite_color = db.Column(db.String(200))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    password_hash=db.Column(db.String(128))


    @property
    def password(self):
        raise AttributeError('Password is not readable!!!!')
    
    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)    

    def __repr__(self):
        return '<Name %r>' % self.name

# Create a form class for adding users
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    favorite_color = StringField("Favorite Color")
    password_hash=PasswordField('Password',validators=[DataRequired(),EqualTo('password_hash2',message='password must match')])
    password_hash2=PasswordField('Confirm Password',validators=[DataRequired()])
    submit = SubmitField("Submit")    


class NameForm(FlaskForm):
    name=StringField("What is your name",validators=[DataRequired()])
    submit=SubmitField("Submit")


class PasswordForm(FlaskForm):
    email=StringField("What is your email",validators=[DataRequired()])
    password_hash=PasswordField("What is your Password",validators=[DataRequired()])
    submit=SubmitField("Submit")


@app.route('/')
def index():
    first_name = "John"
    stuff = "this is bold text"
    favorite_pizza = ["Pepperoni", "Cheese", "Chicken", 41]
    return render_template("index.html", first_name=first_name,
                           stuff=stuff,
                           favorite_pizza=favorite_pizza)

@app.route('/user/<name>')
def user(name):
    return render_template("user.html", user_name=name)

@app.route('/date')
def get_current_date():
    return{"Date":date.today()}


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

@app.route('/name', methods=['GET', 'POST'])
def name():
    name = None
    form = NameForm()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash("Form submitted successfully")
    return render_template("name.html", name=name, form=form)

# test password
@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password= None
    pw_to_check=None
    passed=None

    form = PasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        password=form.password_hash.data
        form.email.data = ''
        form.password_hash.data = ''
        # flash("Form submitted successfully")
        pw_to_check=Users.query.filter_by(email=email).first()
        passed=check_password_hash(pw_to_check.password_hash,password)
    return render_template("test_pw.html", email=email,password=password,pw_to_check=pw_to_check,passed=passed,form=form)

@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            hashed_pw=generate_password_hash(form.password_hash.data, method="pbkdf2:sha256")
            user = Users(name=form.name.data, email=form.email.data,favorite_color=form.favorite_color.data,password_hash=hashed_pw)
            try:
                db.session.add(user)
                db.session.commit()
                flash("User added successfully")
            except Exception as e:
                flash("Error adding user to the database. Please try again.")
                app.logger.error(f"Error adding user: {e}")
        else:
            flash("User already exists")

        # Clear the form fields
        form.name.data = ''
        form.email.data = ''
        form.favorite_color.data=''
        form.password_hash.data=''
    
    users = Users.query.all()  # Get all users
    return render_template("add_user.html", form=form, our_users=users)


@app.route('/update/<int:id>', methods=["GET", "POST"])
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        try:
            db.session.commit()
            flash("User updated successfully")
            return render_template("update.html", form=form, name_to_update=name_to_update)
        except Exception as e:
            flash("Error updating user. Please try again.")
            app.logger.error(f"Error updating user: {e}")
            return render_template("update.html", form=form, name_to_update=name_to_update)
    else:
        return render_template("update.html", form=form, name_to_update=name_to_update)

@app.route('/delete/<int:id>')
def delete(id):
    name=None
    form=UserForm()
    user_to_be_delete=Users.query.get_or_404(id)
    try:
         db.session.delete(user_to_be_delete)
         db.session.commit()
         flash("User deleted successfully")
         users = Users.query.all()  # Get all users
         return render_template("add_user.html", form=form, our_users=users)
    except:
        flash("woops!there is a error!!!!")
        return render_template("add_user.html", form=form, our_users=users)

@app.route('/add_post',methods=['GET','POST'])  
def add_post():
    form=PostForm()
    if form.validate_on_submit():
        post=Posts(title=form.title.data,content=form.content.data,author=form.author.data,slug=form.slug.data)

        form.title.data = '' 
        form.content.data = ''
        form.author.data = ''
        form.slug.data = ''

        db.session.add(post)
        db.session.commit()

        flash("Blog Post submitted successfully")
        return redirect(url_for('add_post'))

    return render_template("add_post.html",form=form)


@app.route('/posts')
def posts():
    posts=Posts.query.order_by(Posts.date_posted)
    return render_template("posts.html",posts=posts)
        

@app.route('/posts/<int:id>')
def post(id):
    post=Posts.query.get_or_404(id)
    return render_template("post.html",post=post)


@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()

    if form.validate_on_submit():
        # Update the existing post with the new data from the form
        post.title = form.title.data
        post.content = form.content.data
        post.author = form.author.data
        post.slug = form.slug.data

        # Commit the changes to the database
        db.session.commit()

        flash("Post updated successfully")

        return redirect(url_for('post', id=post.id))

    # Pre-fill the form with existing post data
    form.title.data = post.title
    form.author.data = post.author
    form.content.data = post.content
    form.slug.data = post.slug

    return render_template("edit.html", form=form)


@app.route('/posts/delete/<int:id>',methods=['POST'])
def delete_post(id):
    post_to_delete=Posts.query.get_or_404(id)
    try:
        db.session.delete(post_to_delete)
        db.session.commit()

        flash("Post deleted")
        posts=Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html",posts=posts)
    except:
        flash("error")
        posts=Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html",posts=posts)
        



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
