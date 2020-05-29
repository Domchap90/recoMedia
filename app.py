import os
from flask import Flask, flash, render_template, redirect, request, session, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

app = Flask(__name__)

app.config["MONGO_DBNAME"] = 'recomediaDB'
from os import path
if path.exists("env.py"):
    import env

app.config["MONGO_URI"] = os.environ.get('MONGO_URI')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

mongo = PyMongo(app)


@app.route('/')
def home(): 
    return render_template("index.html") 

"""
@app.route('/')
@app.route('/user_login', methods=['POST'])
def user_login():
    logins=mongo.db.login
    login_entry=request.form.to_dict()
    
    if logins.find({ 'username':login_entry['username'], 'password':login_entry['password']}):
        return redirect(url_for('userprofile'))
    else:
        return "unfortunately this isn't a valid username or password."
"""


@app.route('/insert_user', methods=['POST','GET'])
def insert_user():
    login_collection = mongo.db.login
    usernames=login_collection.find({},{"username":1})
    username=request.form.get('username')
    password=request.form.get('password')
    print(username+" , "+password)
    if login_collection.find_one({'username':username}):
        flash("Username already exists")
        return redirect(url_for('home'))
    else:
        login_collection.insert_one({'username':username, 'password': password })
        session['username']=username
        return redirect(url_for('userprofile', username=session['username']) )

    return redirect(url_for('home'))

@app.route('/user_profile/<username>')
def userprofile(username):
    return render_template('userprofile.html')

if __name__ == "__main__":
    app.run(host=os.environ.get('IP', '0.0.0.0'),
        port=int(os.environ.get('PORT', "5000")),
        debug=True)