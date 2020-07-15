import os
from datetime import timedelta
from flask import Flask, flash, render_template, redirect, request, session, app, url_for, jsonify
#from flask_socketio import SocketIO, emit
import requests
import math
import re
from flask_pymongo import PyMongo
from pymongo import TEXT
from bson.objectid import ObjectId
from bson.json_util import dumps, loads


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
    film_display=film_rankings({"$match": {} }, 8) # sizing variable
    return render_template("index.html", film_display=film_display) 

@app.before_request
def make_session_permanent():
    # Keeps user logged in for a maximum of 10 mins.
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)
    

@app.route('/username_search_options', methods=['GET'])
def username_search_options():
    login_collection = mongo.db.login
    login_collection.create_index( [ ('username', TEXT) ] )
    search_username=request.args.get('searchValue', '' ,type=str)
    regex=re.compile(search_username, re.IGNORECASE)
    search_suggestions=list(login_collection.find( { 'username' : regex } ).limit(5) ) # limit to 5 suggestions
    search_suggestions_dict=dumps(search_suggestions)

    return jsonify(result=search_suggestions_dict)

@app.route('/login_page')
def login_page(): 
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login(): 
    login_collection = mongo.db.login
    username=request.form.get('username')
    password=request.form.get('password')
    login_query = login_collection.find_one({'username':username})
    if login_query:
        if password==login_query['password']:
            session['username']=username
            session['logged_in'] = True
            return redirect(url_for('userprofile') )
    
    flash("The password or username you entered is incorrect. Please try again.", 'error')
    return redirect(url_for('login_page'))

    #if login_query and 
@app.route('/logout')
def logout(): 
    session.clear()
    session['logged_in'] = False
    return redirect(url_for('home'))

@app.route('/view_user', methods=['POST','GET'])
def view_user():
    username=request.form.get('username')
    login_collection = mongo.db.login
    login_query = login_collection.find_one({'username':username})
    if login_query:
        films_per_page=10       
        top_picks=paginate_query(get_user_films(username), films_per_page)
        new_releases=paginate_query(get_new_releases(username), films_per_page)
        
        return render_template('userview.html', username= username, films=get_user_films(username),
            films_per_page=films_per_page, top_picks= top_picks, new_releases=new_releases )

    else:
        flash("This user doesn't exist.",'error')
    return render_template('userview.html')

@app.route('/user_genre', methods=['GET'])
def user_genre():   
    genre=request.args.get('genre', '' ,type=str)
    username=request.args.get('username', '' ,type=str)
    user_genre_results=paginate_query(get_user_genrefilms(username, genre), 10)
    num_pages= len(user_genre_results)
    genre_dict=dumps(user_genre_results)

    return jsonify(result=genre_dict)
    

def paginate_query(query, items_per_page):
    paginated_list=[]
    # get page size including any partially filled pages (using ceiling function)
    page_size=math.ceil(len(query)/items_per_page)  
    for pages_counted in range(page_size):
        query_page = query[(pages_counted*items_per_page):(pages_counted*items_per_page)+items_per_page]
        paginated_list.append(query_page)
    
    return paginated_list

@app.route('/insert_user', methods=['POST','GET'])
def insert_user():
    login_collection = mongo.db.login
    username=request.form.get('username')
    password=request.form.get('password')
    c_password=request.form.get('c_password')
    error_exists=False
    # Establish if username entered doesn't already exist within the database.
    if login_collection.find_one({'username':username}):
        flash("Username already exists", 'error')
        error_exists=True
    # Ensures username is alphanumeric 
    if re.search("[^a-zA-Z0-9]", username):
        flash("Username must be alphanumeric with no spaces.", 'error')
        error_exists=True
    # Ensures passwords match
    if password!=c_password:
        flash("Passwords do not match", 'error')
        error_exists=True

    if error_exists:
        return redirect(url_for('home'))
    else:
        session['username']=username
        login_collection.insert_one({'username':session['username'], 'password': password })
        session['logged_in'] = True
        return redirect(url_for('userprofile') )

    return redirect(url_for('home'))

@app.route('/userprofile')
def userprofile():
    if session.get('logged_in')==True:
        user_films=get_user_films(session['username'])
        films_per_page=10        
        top_picks=paginate_query( get_user_films(session['username']), films_per_page)
        return render_template('userprofile.html', username=session['username'], films=user_films, top_picks=top_picks, films_per_page=films_per_page)
    else:
        flash("Your login session timed out. Please login again to continue.", 'error')
        return redirect(url_for('login_page') )

def get_user_films(username):
    film_collection=mongo.db.films
    user_films = film_collection.find({'ratings':{'$elemMatch':{ 'username':username}}})
    user_films=list(user_films.sort('ratings.rating',-1))
    return user_films

def get_user_genrefilms(username, genre):
    # Gets films belonging to specific genre for userview page
    film_collection=mongo.db.films
    user_genre_films = film_collection.find({'$and': [{'genre': {'$elemMatch': {"$in": [genre] } } }, {'ratings': {'$elemMatch': { 'username': username } } } ] } )
    user_genre_films=list(user_genre_films.sort('ratings.rating',-1))
    return user_genre_films

def get_new_releases(username):
    film_collection=mongo.db.films
    new_releases = film_collection.find({'$and': [{'year': 2020}, {'ratings':{'$elemMatch': { 'username': username}}}] })
    new_releases = list( new_releases.sort('ratings.rating',-1) )
    return new_releases

@app.route('/insert_rating/<username>', methods=['POST','GET'])
def insert_rating(username):
    form=request.form.to_dict()
    f=request.form
    r=requests.get('https://www.omdbapi.com/?i='+f.get('imdbID')+'&apikey='+app.config['API_KEY'] )
    film_json=r.json()
    poster=film_json['Poster']
    genre=film_json['Genre']
    genre=genre.split(', ')
    if session.get('logged_in')==True:
        film_collection=mongo.db.films
        if film_collection.find_one({'imdbID':f.get('imdbID'), 'ratings':{'$elemMatch':{ 'username':session['username']}}}):
            """ updates rating from DB where film and this user's rating already exist """
            film_collection.update( 
                {'imdbID':f.get('imdbID'), 'ratings.username':session['username'] },
                {'$set': {'ratings.$.rating':int(f.get('rating')), 'ratings.$.review':form['review']} }
                )
        elif film_collection.find_one({'imdbID':f.get('imdbID')}):
            """ inserts rating into pre-existing film which this user hasn't rated yet """
            film_collection.update( 
                {'imdbID':f.get('imdbID') },
                {'$push': { 'ratings' : {'username': session['username'] ,'rating':int(f.get('rating')), 'review':form['review']} }}
                )
            # Rating added for this film. (option 2)
        else:
            """ film not currently listed in db """
            film_collection.insert_one({
                'title': format_title(form['film_title']),'imdbID':form['imdbID'],'year':int(f.get('Year')),'director':f.get('Director'), 
                'cast':f.get('Actors'), 'runtime':f.get('Runtime'), 'genre': genre, 'poster': poster,'ratings':[{'username':session['username'],
                'rating':int(f.get('rating')), 'review':form['review'] }]
                }) 
            # Rating + Film inserted. (option 3)

        user_films = film_collection.find({'ratings':{'$elemMatch':{ 'username':session['username']}}})
        return redirect(url_for('userprofile',username=username, films=user_films))

    else:
        flash("Your login session timed out. Please login again to continue.", 'error')
        return redirect(url_for('login_page') )


@app.route('/delete_rating/<filmID>')
def delete_rating(filmID):
    film_collection=mongo.db.films
    film_to_delete=film_collection.aggregate([
        {'$addFields': {
            'ratingsCount': {'$size':'$ratings'}
            }
        },
        {"$unwind" : "$ratings"},
        {'$match':{'imdbID':filmID}},
        {"$group": {
            "_id":"$imdbID",
            'ratingsCount': { '$first':"$ratingsCount"}
            }
        }
        ])

    for film in film_to_delete:
        ratings_count=film['ratingsCount']
    # Check if user still logged in.
    if session.get('logged_in')==True:
        # if film has only 1 rating, delete entire film document
        if ratings_count==1:
            film_collection.delete_one({'imdbID':filmID})
        # if more than 1 rating for film, simply delete users rating.
        else:
            film_collection.update_one(
                {'imdbID': filmID},
                {'$pull': {'ratings': {'username': session['username']} } } 
            )
        return redirect(url_for('userprofile') )
    else:
        flash("Your login session timed out. Please login again to continue.", 'error')
        return redirect(url_for('login_page') )


@app.route('/show_films/', methods=['POST','GET'])
def show_films():
    overall_rankings=film_rankings({"$match": {} }, 10)
    
    return render_template('films.html', overall_rankings=overall_rankings  )

@app.route('/show_genre_films', methods=['GET'])
def show_genre_films():
    genre=request.args.get('genre', '' ,type=str)
    genre_rankings=film_rankings( {'$match': {'genre':genre } }, 10 )  
    genre_dict=dumps(genre_rankings)

    return jsonify(result=genre_dict)
    

@app.route('/show_director_films', methods=['GET'])
def show_director_films():
    director=request.args.get('director', '' ,type=str)
    director_rankings=film_rankings({'$match': {'director': format_title(director) } }, 10) 
    director_dict=dumps(director_rankings)

    return jsonify(result=director_dict)

@app.route('/show_decade_films', methods=['GET'])
def show_decade_films():
    decade=request.args.get('decade', 0 ,type=int)
    decade_rankings=film_rankings( {'$match':{'year': { '$gte': decade, '$lt': decade+10 } } }, 10) 
    decade_dict=dumps(decade_rankings)

    return jsonify(result=decade_dict)
     

def film_rankings(query, limit):
    film_collection=mongo.db.films
    film_rankings=film_collection.aggregate([
        {'$addFields': {
            'ratingsCount': {'$size':'$ratings'}
            }
        },
        {"$unwind" : "$ratings"},
        {"$unwind" : "$genre"},
        query,
        {"$group": {
            'imdbID': {'$first': '$imdbID' },
            'title' : { '$first': '$title' },
            'year': { '$first': '$year' },
            'poster': { '$first': '$poster'},
            "_id":"$imdbID",
            'ratingsCount': { '$first': "$ratingsCount"},
            "averageRating" : 
                {"$avg" : "$ratings.rating"}
            }},
        { '$sort' : { 'averageRating' : -1, 'ratingsCount': -1}},
        { '$limit': limit }
        ])
    return film_rankings


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


@app.route('/get_reviews/<filmID>/<avgRating>')
def get_reviews(filmID, avgRating):
    film_collection=mongo.db.films
    film=film_collection.find_one({'imdbID': filmID})
    return render_template('reviews.html', film=film, avgRating=avgRating)


if __name__ == "__main__":
    app.run(host=os.environ.get('IP', '0.0.0.0'),
        port=int(os.environ.get('PORT', "5000")),
        debug=True)