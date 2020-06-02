import os
from flask import Flask, flash, render_template, redirect, request, session, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

from os import path
if path.exists("env.py"):
    import env

app = Flask(__name__)
app.config["MONGO_DBNAME"] = 'recomediaDB'
app.config["MONGO_URI"] = os.environ.get('MONGO_URI')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

mongo = PyMongo(app)


@app.route('/')
def home(): 
    return render_template("index.html") 


@app.route('/insert_user', methods=['POST','GET'])
def insert_user():
    login_collection = mongo.db.login
    usernames=login_collection.find({},{"username":1})
    session['username']=request.form.get('username')
    password=request.form.get('password')
    if login_collection.find_one({'username':session['username']}):
        flash("Username already exists", 'error')
        return redirect(url_for('home'))
    else:
        login_collection.insert_one({'username':session['username'], 'password': password })
        film_collection=mongo.db.films
        user_films = film_collection.find({'ratings':{'$elemMatch':{ 'username':session['username']}}})
        return render_template('userprofile.html',username=session['username'],films=user_films)

    return redirect(url_for('home'))

@app.route('/user_profile/<username>/<films>')
def userprofile(username,films):
    film_collection=mongo.db.films
    user_films = film_collection.find({'ratings':{'$elemMatch':{ 'username':session['username']}}})
    return render_template('userprofile.html', username=session['username'], films=user_films)


@app.route('/insert_rating/<username>', methods=['POST','GET'])
def insert_rating(username):
    form=request.form.to_dict()
    film_collection=mongo.db.films
    if film_collection.find_one({'title':form['film_title'], 'ratings':{'$elemMatch':{ 'username':session['username']}}}):
        """ updates rating from DB where film and this user's rating already exist """
        film_collection.update( 
            {'title':form['film_title'], 'ratings.username':session['username'] },
            {'$set': {'title':form['film_title'], 'release_date': form['release_date'],
            'director':form['director'], 'ratings.$.rating':form['rating'], 'ratings.$.review':form['review']} }
            )
    elif film_collection.find_one({'title':form['film_title']}):
        """ inserts rating into pre-existing film which this user hasn't rated yet """
        film_collection.update( 
            {'title':form['film_title'] },
            {'$push': { 'ratings' : {'username': session['username'] ,'rating':form['rating'], 'review':form['review']} }}
            )
    else:
        """ film not currently listed in db """
        film_collection.insert_one({
            'title':form['film_title'],'release_date':form['release_date'],'director':form['director'],
            'ratings':[{'username':session['username'], 'rating':form['rating'], 'review':form['review'] }]
            }) 

    user_films = film_collection.find({'ratings':{'$elemMatch':{ 'username':session['username']}}})
    return redirect(url_for('userprofile',username=username, films=user_films))



if __name__ == "__main__":
    app.run(host=os.environ.get('IP', '0.0.0.0'),
        port=int(os.environ.get('PORT', "5000")),
        debug=True)