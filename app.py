from flask import Flask, render_template, redirect, url_for, request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileRequired, FileAllowed
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/blog'
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key
mongo = PyMongo(app)

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    image = FileField('Image', validators=[
        
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Submit')

@app.route('/')
def home():
    posts = mongo.db.posts.find()
    return render_template('home.html', posts=posts)

@app.route('/post/<id>')
def post(id):
    blog_post = mongo.db.posts.find_one({'_id': ObjectId(id)})
    return render_template('post.html', post=blog_post)

UPLOAD_FOLDER = 'static/uploads'  # Directory to save uploaded images
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/create', methods=['GET', 'POST'])
def create():
    form = PostForm()
    if form.validate_on_submit():
        # Save the uploaded image
        image_file = form.image.data
        filename = secure_filename(image_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(file_path)
        
        # Use forward slashes for the database entry
        mongo.db.posts.insert_one({
            'title': form.title.data,
            'content': form.content.data,
            'image': file_path.replace('\\', '/'),  # Ensure forward slashes
        })
        return redirect(url_for('home'))
    return render_template('create.html', form=form)

@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    form = PostForm()
    blog_post = mongo.db.posts.find_one({'_id': ObjectId(id)})
    
    if form.validate_on_submit():
        # Handle image upload
        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(file_path)
            image_path = file_path.replace('\\', '/')  # Ensure forward slashes
        else:
            image_path = blog_post['image']  # Keep the existing image if not updated

        mongo.db.posts.update_one({'_id': ObjectId(id)}, {
            '$set': {
                'title': form.title.data,
                'content': form.content.data,
                'image': image_path,  # Update image path
            }
        })
        return redirect(url_for('home'))

    form.title.data = blog_post['title']
    form.content.data = blog_post['content']
    
    
    return render_template('edit.html', form=form,blog_post=blog_post)

@app.route('/delete/<id>')
def delete(id):
    mongo.db.posts.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=3000)
