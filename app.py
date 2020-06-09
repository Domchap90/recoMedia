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
#app.config['API_KEY'] = os.environ.get('API_KEY')

mongo = PyMongo(app)
#url = 'http://img.omdbapi.com/?apikey=[yourkey]&'
#datarequest = 'http://www.omdbapi.com/?apikey=[yourkey]&'

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
    print(request.form.to_dict())
    f=request.form
    select_ID=f.get('imdbID')
    select_cast=f.get('Actors')
    select_film=f.get('film_title')
    select_year=f.get('Year')
    print("\n select_ID is "+str(select_ID)+"\n select_cast is "+str(select_cast)+"\n select_film is "+str(select_film)+"\n select_year is "+str(select_year))
    film_collection=mongo.db.films
    if film_collection.find_one({'imdbID':f.get('imdbID'), 'ratings':{'$elemMatch':{ 'username':session['username']}}}):
        """ updates rating from DB where film and this user's rating already exist """
        film_collection.update( 
            {'imdbID':f.get('imdbID'), 'ratings.username':session['username'] },
            {'$set': {'ratings.$.rating':f.get('rating'), 'ratings.$.review':form['review']} }
            )
        print("Rating updated for this film.")
    elif film_collection.find_one({'imdbID':f.get('imdbID')}):
        """ inserts rating into pre-existing film which this user hasn't rated yet """
        film_collection.update( 
            {'imdbID':f.get('imdbID') },
            {'$push': { 'ratings' : {'username': session['username'] ,'rating':f.get('rating'), 'review':form['review']} }}
            )
        print("Rating added for this film. (option 2)")
    else:
        """ film not currently listed in db """
        film_collection.insert_one({
            'title':form['film_title'],'imdbID':form['imdbID'],'year':f.get('Year'),'director':f.get('Director'), 
            'cast':f.get('Actors'), 'runtime':f.get('Runtime'),'ratings':[{'username':session['username'],
            'rating':f.get('rating'), 'review':form['review'] }]
            }) 
        print("Rating + Film inserted. (option 3)")

    user_films = film_collection.find({'ratings':{'$elemMatch':{ 'username':session['username']}}})
    return redirect(url_for('userprofile',username=username, films=user_films))



if __name__ == "__main__":
    app.run(host=os.environ.get('IP', '0.0.0.0'),
        port=int(os.environ.get('PORT', "5000")),
        debug=True)