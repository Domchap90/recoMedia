import os
from flask import Flask, flash, render_template, redirect, request, session, url_for, jsonify
import requests
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

from os import path
if path.exists("env.py"):
    import env

app = Flask(__name__)
app.config["MONGO_DBNAME"] = 'recomediaDB'
app.config["MONGO_URI"] = os.environ.get('MONGO_URI')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['API_KEY'] = os.environ.get('API_KEY')

mongo = PyMongo(app)

@app.route('/')
def home(): 
    return render_template("index.html") 


@app.route('/insert_user', methods=['POST','GET'])
def insert_user():
    login_collection = mongo.db.login
    login_collection.delete_many({})
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
    r=requests.get('https://www.omdbapi.com/?i='+f.get('imdbID')+'&apikey='+app.config['API_KEY'] )
    film_json=r.json()
    poster=film_json['Poster']
    print('poster is '+poster)
    film_collection=mongo.db.films
    if film_collection.find_one({'imdbID':f.get('imdbID'), 'ratings':{'$elemMatch':{ 'username':session['username']}}}):
        """ updates rating from DB where film and this user's rating already exist """
        film_collection.update( 
            {'imdbID':f.get('imdbID'), 'ratings.username':session['username'] },
            {'$set': {'ratings.$.rating':int(f.get('rating')), 'ratings.$.review':form['review']} }
            )
        print("Rating updated for this film.")
    elif film_collection.find_one({'imdbID':f.get('imdbID')}):
        """ inserts rating into pre-existing film which this user hasn't rated yet """
        film_collection.update( 
            {'imdbID':f.get('imdbID') },
            {'$push': { 'ratings' : {'username': session['username'] ,'rating':int(f.get('rating')), 'review':form['review']} }}
            )
        print("Rating added for this film. (option 2)")
    else:
        """ film not currently listed in db """
        film_collection.insert_one({
            'title': format_title(form['film_title']),'imdbID':form['imdbID'],'year':f.get('Year'),'director':f.get('Director'), 
            'cast':f.get('Actors'), 'runtime':f.get('Runtime'), 'poster': poster,'ratings':[{'username':session['username'],
            'rating':int(f.get('rating')), 'review':form['review'] }]
            }) 
        print("Rating + Film inserted. (option 3)")

    user_films = film_collection.find({'ratings':{'$elemMatch':{ 'username':session['username']}}})
    return redirect(url_for('userprofile',username=username, films=user_films))

@app.route('/show_films', methods=['GET'])
def show_films():
    film_collection=mongo.db.films
    film_rankings=film_collection.aggregate([
        {'$addFields': {
            'ratingsCount': {'$size':'$ratings'}
            }
        },
        {"$unwind" : "$ratings"},
        {"$group": {
            'title' : { '$first': '$title' },
            'year': { '$first': '$year' },
            "_id":"$imdbID",
            'ratingsCount': { '$first':"$ratingsCount"},
            "averageRating" : 
                {"$avg" : "$ratings.rating"}
            }},
        { '$sort' : { 'averageRating' : -1, 'ratingsCount': -1}},
        ])

    return render_template('films.html', film_rankings=film_rankings)

def format_title(title):
    """ Formats film titles so that the capitalization of each word is consistent with imdb formatting rules"""
    title=title.lower()
    # list of smaller words that are NOT capitalized in the middle of titles (but are capitalized if they are first/last word )
    exceptions=["a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with"]
    title_words=title.split()
    formatted_title=[]
    ind=0
     
    for word in title_words:
        if word in exceptions and title_words.index(word,ind)>0 and title_words.index(word,ind)<len(title_words)-1: 
            formatted_title.append(word)
        else:
            formatted_title.append(word.capitalize())
        ind=ind+1

    return " ".join(formatted_title)

if __name__ == "__main__":
    app.run(host=os.environ.get('IP', '0.0.0.0'),
        port=int(os.environ.get('PORT', "5000")),
        debug=True)