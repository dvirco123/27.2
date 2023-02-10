"""SQLAlchemy models for blogly."""

import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

DEFAULT_IMAGE_URL = "https://www.freeiconspng.com/uploads/icon-user-blue-symbol-people-person-generic--public-domain--21.png"


class User(db.Model):
    """Site user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text, nullable=False, default=DEFAULT_IMAGE_URL)

    posts = db.relationship("Post", backref="user", cascade="all, delete-orphan")

    @property
    def full_name(self):
        """Return full name of user."""

        return f"{self.first_name} {self.last_name}"


class Post(db.Model):
    """Blog post."""

    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @property
    def friendly_date(self):
        """Return nicely-formatted date."""

        return self.created_at.strftime("%a %b %-d  %Y, %-I:%M %p")


class PostTag(db.Model):
    """Tag on a post."""

    __tablename__ = "posts_tags"

    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)


class Tag(db.Model):
    """Tag that can be added to posts."""

    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False, unique=True)

    posts = db.relationship(
        'Post',
        secondary="posts_tags",
        # cascade="all,delete",
        backref="tags",
    )


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
part-three/app.py
from flask import Flask, request, redirect, render_template, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Post, Tag

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///blogly"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ihaveasecret'

# Having the Debug Toolbar show redirects explicitly is often useful;
# however, if you want to turn it off, you can uncomment this line:
#
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()


@app.route('/')
def root():
    """Show recent list of posts, most-recent first."""

    posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return render_template("posts/homepage.html", posts=posts)


@app.errorhandler(404)
def page_not_found(e):
    """Show 404 NOT FOUND page."""

    return render_template('404.html'), 404


##############################################################################
# User route

@app.route('/users')
def users_index():
    """Show a page with info on all users"""

    users = User.query.order_by(User.last_name, User.first_name).all()
    return render_template('users/index.html', users=users)


@app.route('/users/new', methods=["GET"])
def users_new_form():
    """Show a form to create a new user"""

    return render_template('users/new.html')


@app.route("/users/new", methods=["POST"])
def users_new():
    """Handle form submission for creating a new user"""

    new_user = User(
        first_name=request.form['first_name'],
        last_name=request.form['last_name'],
        image_url=request.form['image_url'] or None)

    db.session.add(new_user)
    db.session.commit()
    flash(f"User {new_user.full_name} added.")

    return redirect("/users")


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show a page with info on a specific user"""

    user = User.query.get_or_404(user_id)
    return render_template('users/show.html', user=user)


@app.route('/users/<int:user_id>/edit')
def users_edit(user_id):
    """Show a form to edit an existing user"""

    user = User.query.get_or_404(user_id)
    return render_template('users/edit.html', user=user)


@app.route('/users/<int:user_id>/edit', methods=["POST"])
def users_update(user_id):
    """Handle form submission for updating an existing user"""

    user = User.query.get_or_404(user_id)
    user.first_name = request.form['first_name']
    user.last_name = request.form['last_name']
    user.image_url = request.form['image_url']

    db.session.add(user)
    db.session.commit()
    flash(f"User {user.full_name} edited.")

    return redirect("/users")


@app.route('/users/<int:user_id>/delete', methods=["POST"])
def users_destroy(user_id):
    """Handle form submission for deleting an existing user"""

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.full_name} deleted.")

    return redirect("/users")


##############################################################################
# Posts route


@app.route('/users/<int:user_id>/posts/new')
def posts_new_form(user_id):
    """Show a form to create a new post for a specific user"""

    user = User.query.get_or_404(user_id)
    tags = Tag.query.all()
    return render_template('posts/new.html', user=user, tags=tags)


@app.route('/users/<int:user_id>/posts/new', methods=["POST"])
def posts_new(user_id):
    """Handle form submission for creating a new post for a specific user"""

    user = User.query.get_or_404(user_id)
    tag_ids = [int(num) for num in request.form.getlist("tags")]
    tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

    new_post = Post(title=request.form['title'],
                    content=request.form['content'],
                    user=user,
                    tags=tags)

    db.session.add(new_post)
    db.session.commit()
    flash(f"Post '{new_post.title}' added.")

    return redirect(f"/users/{user_id}")


@app.route('/posts/<int:post_id>')
def posts_show(post_id):
    """Show a page with info on a specific post"""

    post = Post.query.get_or_404(post_id)
    return render_template('posts/show.html', post=post)


@app.route('/posts/<int:post_id>/edit')
def posts_edit(post_id):
    """Show a form to edit an existing post"""

    post = Post.query.get_or_404(post_id)
    tags = Tag.query.all()
    return render_template('posts/edit.html', post=post, tags=tags)


@app.route('/posts/<int:post_id>/edit', methods=["POST"])
def posts_update(post_id):
    """Handle form submission for updating an existing post"""

    post = Post.query.get_or_404(post_id)
    post.title = request.form['title']
    post.content = request.form['content']

    tag_ids = [int(num) for num in request.form.getlist("tags")]
    post.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

    db.session.add(post)
    db.session.commit()
    flash(f"Post '{post.title}' edited.")

    return redirect(f"/users/{post.user_id}")


@app.route('/posts/<int:post_id>/delete', methods=["POST"])
def posts_destroy(post_id):
    """Handle form submission for deleting an existing post"""

    post = Post.query.get_or_404(post_id)

    db.session.delete(post)
    db.session.commit()
    flash(f"Post '{post.title} deleted.")

    return redirect(f"/users/{post.user_id}")


##############################################################################
# Tags route


@app.route('/tags')
def tags_index():
    """Show a page with info on all tags"""

    tags = Tag.query.all()
    return render_template('tags/index.html', tags=tags)


@app.route('/tags/new')
def tags_new_form():
    """Show a form to create a new tag"""

    posts = Post.query.all()
    return render_template('tags/new.html', posts=posts)


@app.route("/tags/new", methods=["POST"])
def tags_new():
    """Handle form submission for creating a new tag"""

    post_ids = [int(num) for num in request.form.getlist("posts")]
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    new_tag = Tag(name=request.form['name'], posts=posts)

    db.session.add(new_tag)
    db.session.commit()
    flash(f"Tag '{new_tag.name}' added.")

    return redirect("/tags")


@app.route('/tags/<int:tag_id>')
def tags_show(tag_id):
    """Show a page with info on a specific tag"""

    tag = Tag.query.get_or_404(tag_id)
    return render_template('tags/show.html', tag=tag)


@app.route('/tags/<int:tag_id>/edit')
def tags_edit_form(tag_id):
    """Show a form to edit an existing tag"""

    tag = Tag.query.get_or_404(tag_id)
    posts = Post.query.all()
    return render_template('tags/edit.html', tag=tag, posts=posts)


@app.route('/tags/<int:tag_id>/edit', methods=["POST"])
def tags_edit(tag_id):
    """Handle form submission for updating an existing tag"""

    tag = Tag.query.get_or_404(tag_id)
    tag.name = request.form['name']
    post_ids = [int(num) for num in request.form.getlist("posts")]
    tag.posts = Post.query.filter(Post.id.in_(post_ids)).all()

    db.session.add(tag)
    db.session.commit()
    flash(f"Tag '{tag.name}' edited.")

    return redirect("/tags")


@app.route('/tags/<int:tag_id>/delete', methods=["POST"])
def tags_destroy(tag_id):
    """Handle form submission for deleting an existing tag"""

    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash(f"Tag '{tag.name}' deleted.")

    return redirect("/tags")
Templates: Posts
part-three/templates/posts/show.html
{% extends 'base.html' %}

{% block title %}{{ post.title }}{% endblock %}

{% block content %}

<h1>{{ post.title }}</h1>

<p>{{ post.content }}</p>
<p><i>By {{ post.user.full_name }}
  on {{ post.friendly_date }}
</i></p>

{% if post.tags %}
<p>
  <b>Tags:</b>
  {% for tag in post.tags %}
  <a href="/tags/{{ tag.id }}"><i class="badge badge-primary">{{ tag.name }}</i></a>
  {% endfor %}
</p>
{% endif %}

<form>
  <button class="btn btn-outline-primary"
          formmethod="GET"
          formaction="/users/{{ post.user_id }}">Cancel
  </button>
  <button class="btn btn-primary"
          formmethod="GET"
          formaction="/posts/{{ post.id }}/edit">Edit
  </button>
  <button class="btn btn-danger"
          formmethod="POST"
          formaction="/posts/{{ post.id }}/delete">Delete
  </button>
</form>

{% endblock %}
part-three/templates/posts/new.html
{% extends 'base.html' %}

{% block title %}Add Post{% endblock %}

{% block content %}

<h1>Add Post for {{ user.full_name }}</h1>

<form method="POST">

  <div class="form-group row">
    <label for="title" class="col-sm-2 col-form-label">Title</label>
    <div class="col-sm-10">
      <input class="form-control" id="title" name="title">
    </div>
  </div>

  <div class="form-group row">
    <label for="content" class="col-sm-2 col-form-label">Content</label>
    <div class="col-sm-10">
      <textarea class="form-control" id="content" name="content"></textarea>
    </div>
  </div>

  <div class="form-check">
    {% for tag in tags %}
    <div>
      <input class="form-check-input"
             type="checkbox"
             value="{{ tag.id }}"
             id="tag_{{ tag.id }}"
             name="tags">
      <label class="form-check-label" for="tag_{{ tag.id }}">
        {{ tag.name }}
      </label>
    </div>
    {% endfor %}
  </div>

  <div class="form-group row">
    <div class="ml-auto mr-3">
      <a href="/users/{{ user.id }}" class="btn btn-info">Cancel</a>
      <button type="submit" class="btn btn-success">Add</button>
    </div>
  </div>

</form>

{% endblock %}
part-three/templates/posts/edit.html
{% extends 'base.html' %}

{% block title %}Edit Post{% endblock %}

{% block content %}

<h1>Edit Post</h1>

<form method="POST" action="/posts/{{ post.id }}/edit">

  <div class="form-group row">
    <label for="title" class="col-sm-2 col-form-label">Title</label>
    <div class="col-sm-10">
      <input class="form-control" id="title" name="title" value="{{ post.title }}">
    </div>
  </div>

  <div class="form-group row">
    <label for="content" class="col-sm-2 col-form-label">Post Content</label>
    <div class="col-sm-10">
      <textarea class="form-control"
                id="content"
                name="content">{{ post.content }}</textarea>
    </div>
  </div>

  <div class="form-check">
    {% for tag in tags %}
    <div>
      <input class="form-check-input"
             type="checkbox"
             value="{{ tag.id }}"
             id="tag_{{ tag.id }}"
             {% if tag in post.tags %}checked{% endif %}
             name="tags">
      <label class="form-check-label" for="tag_{{ tag.id }}">
        {{ tag.name }}
      </label>
    </div>
    {% endfor %}
  </div>

  <div class="form-group row">
    <div class="ml-auto mr-3">
      <a href="/users/{{ post.user_id }}" class="btn btn-outline-info">
        Cancel
      </a>
      <button type="submit" class="btn btn-success">
        Edit
      </button>
    </div>
  </div>

</form>

{% endblock %}
part-three/templates/posts/homepage.html
{% extends 'base.html' %}

{% block title %}Blogly{% endblock %}

{% block content %}

<h1>Blogly Recent Posts</h1>

{% for post in posts %}
<h2 class="mt-4">
  <a href="/posts/{{ post.id }}">{{ post.title }}</a>
</h2>
<p>{{ post.content }}</p>
<p>
  <small>By {{ post.user.full_name }} on {{ post.friendly_date }}</small>
</p>

{% if post.tags %}
<p>
  <b>Tags:</b>
  {% for tag in post.tags %}
  <a href="/tags/{{ tag.id }}"><i class="badge badge-primary">{{ tag.name }}</i></a>
  {% endfor %}
</p>
{% endif %}

{% endfor %}

{% endblock %}}
Templates: Tags
part-three/templates/tags/show.html
{% extends 'base.html' %}

{% block title %}{{ tag.name }}{% endblock %}

{% block content %}

<h1>{{ tag.name }}</h1>

<ul>
  {% for post in tag.posts %}
  <li><a href="/posts/{{ post.id }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>

<form>
  <button formmethod="GET"
          formaction="/tags/{{ tag.id }}/edit"
          class="btn btn-primary">Edit
  </button>
  <button formmethod="POST"
          formaction="/tags/{{ tag.id }}/delete"
          class="btn btn-danger">Delete
  </button>

</form>
{% endblock %}
part-three/templates/tags/new.html
{% extends 'base.html' %}

{% block title %}Add Tag{% endblock %}

{% block content %}

<h1>Create a tag</h1>

<form method="POST" action="/tags/new">

  <div class="form-group row">
    <label for="name" class="col-sm-2 col-form-label d-flex align-items-center">
      Name
    </label>
    <div class="col-sm-10">
      <input type="text" class="form-control" id="name" name="name"
             placeholder="Enter a name for the tag">
    </div>
  </div>

  <div class="form-check form-group row">
    {% for post in posts %}
    <div>
      <input class="form-input"
             type="checkbox"
             value="{{ post.id }}"
             id="post_{{ post.id }}"
             name="posts">
      <label class="form-check-label" for="post_{{ post.id }}">
        {{ post.title }}
      </label>
    </div>
    {% endfor %}
  </div>

  <div class="mt-3 form-group row">
    <div class="ml-auto mr-3">
      <a href="/tags" class="btn btn-outline-primary">Cancel</a>
      <button type="submit" class="btn btn-success">Add</button>
    </div>
  </div>

</form>

{% endblock %}
part-three/templates/tags/edit.html
{% extends 'base.html' %}

{% block title %}Edit Tag{% endblock %}

{% block content %}

<h1>Edit a tag</h1>

<form method="POST" action="/tags/{{ tag.id }}/edit">

  <div class="form-group row">
    <label for="name" class="col-sm-2 col-form-label d-flex align-items-center">
      Name
    </label>
    <div class="col-sm-10">
      <input type="text" 
             class="form-control" 
             id="name" 
             name="name" 
             placeholder="Enter a name for the tag"
             value="{{ tag.name }}">
    </div>
  </div>

  <div class="form-group row form-check">
    {% for post in posts %}
    <div>
      <input
              class="form-input"
              type="checkbox"
              value="{{ post.id }}"
              id="post_{{ post.id }}"
              name="posts"
              {% if post in tag.posts %}
              checked
              {% endif %}
      >
      <label class="form-check-label" for="post_{{ post.id }}">
        {{ post.title }}
      </label>
    </div>
    {% endfor %}
  </div>

  <div class="mt-3 form-group row">
    <div class="ml-auto mr-3">
      <a href="/tags" class="btn btn-info">Cancel</a>
      <button type="submit" class="btn btn-success">Edit</button>
    </div>

  </div>

</form>

{% endblock %}
part-three/templates/tags/index.html
{% extends 'base.html' %}

{% block title %}Tags{% endblock %}

{% block content %}

<h1>Tags</h1>

<ul>
  {% for tag in tags %}
  <li><a href="/tags/{{ tag.id }}">{{ tag.name }}</a></li>
  {% endfor %}
</ul>

<p><a class="btn btn-primary" href="/tags/new">Add Tag</a></p>

{% endblock %}