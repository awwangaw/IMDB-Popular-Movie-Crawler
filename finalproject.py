from pickle import POP
from xml.etree.ElementPath import find
import requests
import json
from bs4 import BeautifulSoup
import sqlite3
import plotly.graph_objects as go
import math
from collections import deque
from flask import Flask, render_template, request, flash
from flask_wtf import Form
from wtforms import SelectField, SubmitField, validators, ValidationError
app = Flask(__name__)
app.secret_key = 'development key'


IMDB_BASE_URL = 'https://www.imdb.com'
MOST_POPULAR_MOVIES_LIST_URL = 'https://www.imdb.com/chart/moviemeter/?ref_=nv_mv_mpm'

CACHE_FILE_NAME = 'movies_cache.json'
MOVIE_CACHE = {} # key: URL, value: entire page

POPULAR_FILMS_DICT = {} # key: movie, value: dictonary with additional movie information

GRAPH = {} # graph of actors to movies and movies to actors
GRAPH_JSON_FILE_NAME = 'graph.json'

def generate_unique_key(url):
    return url

def store_in_cache_file(cache):
    cache_content = json.dumps(cache)
    cache_file = open(CACHE_FILE_NAME, 'w')
    cache_file.write(cache_content)
    cache_file.close()

def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_content = cache_file.read()
        cache = json.loads(cache_content)
        cache_file.close()
    except:
        cache = {}
    return cache


MOVIE_CACHE = load_cache()

def make_request_using_cache(url):
    request_key = generate_unique_key(url)
    if request_key in MOVIE_CACHE.keys():
        print("Using the information in cache")
        return MOVIE_CACHE[request_key]
    else:
        print("Retrieving information from website")
        response = requests.get(url)
        MOVIE_CACHE[request_key] = response.text
        store_in_cache_file(MOVIE_CACHE)
        return MOVIE_CACHE[request_key]

def scrape_list_of_popular_movies():
    starting_page = make_request_using_cache(MOST_POPULAR_MOVIES_LIST_URL)
    soup_list = BeautifulSoup(starting_page, 'html.parser')
    #list_of_movie_elements = soup_list.find_all(class_ = 'posterColumn')
    list_of_movie_elements = soup_list.find_all("td", {"class": "posterColumn"})

    for movie in list_of_movie_elements:
        url_suffix = movie.find('a')['href']
        full_link = IMDB_BASE_URL + url_suffix
        img_prep = movie.find('img')
        movie_name = img_prep.get('alt', '')
        POPULAR_FILMS_DICT[movie_name] = {}
        POPULAR_FILMS_DICT[movie_name]['full_link'] = full_link
        POPULAR_FILMS_DICT[movie_name]['movie_name'] = movie_name
        ranking = movie.find("span").attrs['data-value']
        ranking = movie.find("span").attrs['data-value']
        POPULAR_FILMS_DICT[movie_name]['ranking'] = ranking

def store_in_cache_file_test_tbr(cache):
    cache_content = json.dumps(cache)
    cache_file = open('second_part_script', 'w')
    cache_file.write(cache_content)
    cache_file.close()



def scrape_second_webpage():
    temp_list = []
    for film in POPULAR_FILMS_DICT:
        url_link = POPULAR_FILMS_DICT[film]['full_link']
        response_page = make_request_using_cache(url_link)
        second_page_soup = BeautifulSoup(response_page, 'html.parser')
        film_dict = json.loads("".join(second_page_soup.find("script",{"type":"application/ld+json"}).contents))
        try:
            actors = []
            for actor in film_dict['actor']:
                actors.append(actor['name'])

            GRAPH[film] = actors # constructing graph: film to actors

            POPULAR_FILMS_DICT[film]['actor'] = actors

            directors = []
            for director in film_dict['director']:
                directors.append(director['name'])

            POPULAR_FILMS_DICT[film]['director'] = directors

            writers = []
            for writer in film_dict['creator']:
                try:
                    writers.append(writer['name'])
                except:
                    None

            POPULAR_FILMS_DICT[film]['writer'] = writers

            POPULAR_FILMS_DICT[film]['datePublished'] = film_dict['datePublished']

            genres = film_dict['genre']
            POPULAR_FILMS_DICT[film]['genre'] = genres
        except:
            temp_list.append(film)
    for element in temp_list:
        del POPULAR_FILMS_DICT[element]

# constructing graph: actor to films
def constructing_graph_actor_to_movies():
    db_connection = sqlite3.connect(DATABASE_NAME)
    db_cursor = db_connection.cursor()

    actor_movies = '''
            SELECT ActorName, MovieName FROM actors ORDER BY ActorName;
    '''
    query_result = db_cursor.execute(actor_movies)
    query_result = list(db_cursor.fetchall())

    for actor_movie in query_result:
        if actor_movie[0] in GRAPH:
            GRAPH[actor_movie[0]].append(actor_movie[1])
        else:
            GRAPH[actor_movie[0]] = [actor_movie[1]]

    db_connection.commit()
    db_connection.close()

def write_graph_to_json_file():
    graph_content = json.dumps(GRAPH)
    graph_file = open(GRAPH_JSON_FILE_NAME, 'w')
    graph_file.write(graph_content)
    graph_file.close()

def find_shortest_path(graph, start, end):
        dist = {start: [start]}
        q = deque([start])
        while len(q):
            at = q.popleft()
            for next in graph[at]:
                if next not in dist:
                    dist[next] = dist[at] + [next]
                    q.append(next)

        return dist.get(end)


'''
Create Database
'''
DATABASE_NAME = 'popular_movies.db'

def create_database():
    db_connection = sqlite3.connect(DATABASE_NAME)
    db_cursor = db_connection.cursor()

    drop_movie_sql = '''
        DROP TABLE IF EXISTS 'movies';
    '''

    drop_actor_sql = '''
        DROP TABLE IF EXISTS 'actors';
    '''

    drop_director_sql = '''
        DROP TABLE IF EXISTS 'directors';
    '''

    create_movie_sql = '''
        CREATE TABLE 'movies' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Rank' INTEGER,
                'Name' TEXT NOT NULL,
                'AverageRating' REAL,
                'ContentRating' TEXT NOT NULL,
                'PublishedDate' DATE,
                'Genre' TEXT
        );
    '''
    db_cursor.execute(drop_movie_sql)
    db_cursor.execute(create_movie_sql)


    create_actor_sql = '''
        CREATE TABLE 'actors' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'MovieName' TEXT NOT NULL,
            'ActorName' TEXT NOT NULL,
            FOREIGN KEY(MovieName) REFERENCES movies(Name)
        )
    '''
    db_cursor.execute(drop_actor_sql)
    db_cursor.execute(create_actor_sql)


    create_director_sql = '''
        CREATE TABLE 'directors' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'MovieName' TEXT NOT NULL,
            'DirectorName' TEXT NOT NULL,
            FOREIGN KEY(MovieName) REFERENCES movies(Name)
        )
    '''
    db_cursor.execute(drop_director_sql)
    db_cursor.execute(create_director_sql)

    db_connection.commit()
    db_connection.close()


def load_movies():
    db_connection = sqlite3.connect(DATABASE_NAME)
    db_cursor = db_connection.cursor()

    insert_movie = '''
            INSERT INTO 'movies' ('Name', 'Rank', 'ContentRating', 'PublishedDate', 'Genre')
            VALUES (?, ?, ?, ?, ?)
    '''
    for movie in POPULAR_FILMS_DICT:
        genre = ','.join(POPULAR_FILMS_DICT[movie]['genre'])
        fields = (POPULAR_FILMS_DICT[movie]['movie_name'], POPULAR_FILMS_DICT[movie]['ranking'], 'A', POPULAR_FILMS_DICT[movie]['datePublished'], genre)
        db_cursor.execute(insert_movie, fields)

    #db_cursor.execute("SELECT * FROM 'movies'")
    db_connection.commit()
    db_connection.close()

def load_actors():
    db_connection = sqlite3.connect(DATABASE_NAME)
    db_cursor = db_connection.cursor()

    insert_actor = '''
            INSERT INTO 'actors' ('MovieName', 'ActorName')
            VALUES (?, ?)
    '''
    for movie in POPULAR_FILMS_DICT:
        movie_name = POPULAR_FILMS_DICT[movie]['movie_name']
        for actor in POPULAR_FILMS_DICT[movie]['actor']:
            fields = (movie_name, actor)
            db_cursor.execute(insert_actor, fields)

    db_connection.commit()
    db_connection.close()

def load_directors():
    db_connection = sqlite3.connect(DATABASE_NAME)
    db_cursor = db_connection.cursor()

    insert_director = '''
            INSERT INTO 'directors' ('MovieName', 'DirectorName')
            VALUES (?, ?)
    '''

    for movie in POPULAR_FILMS_DICT:
        movie_name = POPULAR_FILMS_DICT[movie]['movie_name']
        for director in POPULAR_FILMS_DICT[movie]['director']:
            fields = (movie_name, director)
            db_cursor.execute(insert_director, fields)

    db_connection.commit()
    db_connection.close()

@app.route('/')
def home():
    return render_template("home.html")

# Pie chart for genre breakdown
@app.route('/genre')
def plot_genre():
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()

    statement = '''
        SELECT Name, Genre from movies;
    '''

    query_result = cur.execute(statement)
    query_result = list(cur.fetchall())

    genre_count_dict = {}
    #movie_genre_list = []
    for n,g in query_result:
        genre_list = g.split(",")
        for genre in genre_list:
            #movie_genre_list.append((n,genre))
            if genre not in genre_count_dict:
                genre_count_dict[genre] = 1
            else:
                genre_count_dict[genre] = genre_count_dict[genre] + 1
    print(genre_count_dict)

    labels = list(genre_count_dict.keys())
    values = list(genre_count_dict.values())

    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.update_layout(
    title={
        'text': "Percentage of Popular Movies by Genre",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    fig.show()

    conn.close()

# line plot for number of movies released each month
@app.route('/month')
def plot_movies_each_month():
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()

    statement = '''
        select strftime('%m', PublishedDate) as Month, count(*) from movies group by Month order by Month ASC;
    '''

    query_result = cur.execute(statement)
    query_result = list(cur.fetchall())

    labels = []
    values = []
    labels_month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for m,c in query_result:
        labels.append(m)
        values.append(c)


    fig = go.Figure(data=go.Scatter(x=labels_month_name, y=values))
    fig.update_layout(
    title={
        'text': "Number of Popular Movies Released Each Month",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    fig.show()

# line chart for number of movies released each year
@app.route('/year')
def plot_actors_in_movies():
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()

    statement = '''
        select strftime('%Y', PublishedDate) as Year, count(*) from movies group by Year order by Year;
    '''

    query_result = cur.execute(statement)
    query_result = list(cur.fetchall())

    labels = []
    values = []
    for element in query_result:
        labels.append(element[0])
        values.append(element[1])

    fig = go.Figure([go.Bar(x=labels, y=values, text=values, textposition='auto')])
    fig.update_layout(
    title={
        'text': "Number of Popular Movies Released Per Year",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    fig.show()

    conn.close()


# Bar graph for director's who have released more than 1 movie and their average ranking of movies
@app.route('/director')
def plot_director_count():
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()

    statement = '''
        SELECT DirectorName, Name, ROUND(AVG(Rank), 2) AS AverageRank, COUNT(*) AS NumberOfMovies
        FROM directors LEFT JOIN movies ON directors.MovieName = movies.Name
        GROUP BY DirectorName
        HAVING NumberOfMovies > 1
        ORDER BY AverageRank, DirectorName DESC
        ;
    '''
    query_result = cur.execute(statement)
    query_result = list(cur.fetchall())

    conn.close()

    director_lst = []
    rank_lst = []
    for i in query_result:
        director_lst.append(i[0])
        rank_lst.append(i[2])

    fig = go.Figure([go.Bar(x=director_lst, y=rank_lst, text=rank_lst, textposition='auto')])
    fig.update_layout(
    title={
        'text': "Directors who have more than 1 Popular Movie and Their Movie's Average Ranking",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    fig.show()

######### Form ############
class ActorForm(Form):
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()

    statement = '''
        SELECT distinct ActorName from actors;
    '''
    query_result = cur.execute(statement)
    query_result = list(cur.fetchall())

    conn.close()

    actor_list = []
    for element in query_result:
        actor_list.append(element[0])

    actor1 = SelectField(coerce=str, label="Name of first actor", choices = actor_list)
    actor2 = SelectField(coerce=str, label="Name of second actor", choices = actor_list)

    submit = SubmitField("Submit")

######### Form View ###########
@app.route('/game', methods = ['GET', 'POST'])
def check_two_actors_in_same_movie():
    form = ActorForm(request.form)

    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.' + str(form.actor1))
            return render_template('actor.html', form=form)
        else:
            #flash('Success. Actor1 value: ' + str(form.actor1.data))
            #flash('Success. Actor2 value: ' + str(form.actor2.data))
            shortest_path = find_shortest_path(GRAPH, form.actor1.data, form.actor2.data)
            if shortest_path is not None:
                degree = math.floor(len(shortest_path)/2)
                if degree == 1:
                    flash(shortest_path[0] + ' and ' + shortest_path[2] + ' have acted in the same popular movie: ' + str(shortest_path[1]))
                else:
                    flash(shortest_path[0] + ' and ' + shortest_path[2] + ' have not acted in the same popular movie.')
            else:
                flash(form.actor1.data + ' and ' + form.actor2.data + ' have not acted in the same popular movie.')

            return render_template('success.html')
    else:
        #request.method == 'GET':
        return render_template('actor.html', form=form)



if __name__=="__main__":
    create_database()
    #make_request_using_cache(MOST_POPULAR_MOVIES_LIST_URL)
    scrape_list_of_popular_movies()
    scrape_second_webpage()
    load_movies()
    load_actors()
    load_directors()
    constructing_graph_actor_to_movies()
    write_graph_to_json_file()
    #print(GRAPH)
    #print(find_shortest_path(GRAPH, 'Nicole Kidman', 'Claes Bang'))
    app.run(debug=True)
    #plot_director_count()
    #print(MOVIE_CACHE)
    #print(POPULAR_FILMS_DICT)