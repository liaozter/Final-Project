#################################
##### Name: Zitong Liao
##### Uniqname: liaozt
#################################
import sqlite3
import csv
import json
import requests
import secret

# Define constants
DBNAME = 'media.db'
BECHDELCSV = 'movies.csv'
CACHE_FNAME = 'media_cache.json'

# Define class
class Media:

    def __init__(self, title="No Title", author="No Author", year="No Release Year", summary="None"):
        self.title = title
        self.author = author
        self.year = year
        self.summary = summary

    def __str__(self):
        return self.title + " by " + self.author + " (" + self.year + ")"


class Movie (Media):

    def __init__(self, title="No Title", author="No Author", year="No Release Year",
                 summary="None", rating="No Rating", genres="None", img_url="None", status="No Data"):

        super().__init__(title, author, year, summary)
        self.rating = rating
        self.genres = genres
        self.img_url = img_url
        self.status = status

    def __str__(self):
        return super().__str__() + " [" + self.rating + "]"


class Book (Media):
    def __init__(self, title="No Title", author="No Author", year="No Release Year",
                 summary="None", pages=0):
        super().__init__(title, author, year, summary)
        self.pages = pages

    def __str__(self):
        return super().__str__() + " [" + str(self.pages) + "]"


# Initialize cache file
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}


# Initialize media.db file (creating tables for Books, Movies, and BechdelStats.)
def init_db():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    # Drop tables
    statement = '''
        DROP TABLE IF EXISTS 'Books';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'Movies';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'BechdelStats';
    '''
    cur.execute(statement)

    conn.commit()

    # Create tables
    statement = '''
        CREATE TABLE Books (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT NOT NULL, 
            Year TEXT NOT NULL,
            Author TEXT NOT NULL,
            Description BLOB,
            MovieId INTEGER,
            FOREIGN KEY(MovieId) REFERENCES Movie(Id)
        );
    '''
    cur.execute(statement)

    statement = '''
            CREATE TABLE Movies (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Title TEXT NOT NULL, 
                Year TEXT NOT NULL,
                Director TEXT NOT NULL,
                Rating TEXT,
                Genre TEXT,
                Plot BLOB,
                PosterURL TEXT,
                BechdelId INTEGER NOT NULL,
                FOREIGN KEY(BechdelId) REFERENCES BechdelStats(Id)
            );
        '''
    cur.execute(statement)

    statement = '''
        CREATE TABLE BechdelStats (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT NOT NULL,
            Year INT NOT NULL, 
            Status TEXT NOT NULL,
            Budget REAL NOT NULL,
            GrossIncome REAL NOT NULL
        );
    '''
    cur.execute(statement)

    conn.commit()
    conn.close()



# Read CSV file into media.db
def insert_bechdel_stats_into_db():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    # Insert data to Bechdel Stats table
    with open(BECHDELCSV, encoding='utf-8') as csv_data_file:
        csv_reader = csv.reader(csv_data_file)
        next(csv_reader)

        for bechdel_movie in csv_reader:
            year = bechdel_movie[0]
            title = bechdel_movie[2]
            status = bechdel_movie[5]
            budget = bechdel_movie[6]
            gross = bechdel_movie[7]

            insertion = (None, title, year, status, budget, gross)
            statement = 'INSERT INTO "BechdelStats" '
            statement += 'VALUES (?, ?, ?, ?, ?, ?)'

            cur.execute(statement, insertion)
            conn.commit()

    conn.close()



# Make requests to Open Movie Database API for movies on the Bechdel list into media.db.
def insert_movies_into_db():
    titles_list = []
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    titles_list = get_bechdel_titles(cur, titles_list)

    for title in titles_list:
        movie_resp = make_request_using_cache(title[0], "movie")

        if movie_resp["Response"] == "True" and title[0] == movie_resp["Title"]:

            #Look up foreign key for BechdelId in BechdelStats table
            statement = "SELECT Id FROM BechdelStats WHERE Title=?"
            result = cur.execute(statement, (movie_resp["Title"],))
            for row in result:
                bechdel_id = int(row[0])

            insertion = (None, movie_resp["Title"], movie_resp["Year"], movie_resp["Director"], movie_resp["Rated"],
                   movie_resp["Genre"], movie_resp["Plot"], movie_resp["Poster"], bechdel_id)
            statement = 'INSERT INTO "Movies" '
            statement += "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            cur.execute(statement, insertion)
            conn.commit()

    conn.close()



# Make requests to Google Books API for books on the Bechdel list
def insert_books_into_db():
    titles_list = []
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    book_is_found = False

    #titles_list = get_bechdel_titles(cur, titles_list)
    statement = "SELECT Movies.Title FROM Movies"
    results = cur.execute(statement)
    movie_titles_tuple = results.fetchall()

    #Process title data by converting immutable tuple to mutable list
    for title in movie_titles_tuple:
        titles_list.append(list(title))

    for title in titles_list:
        title[0]=title[0].replace(" ", "-")

    for title in titles_list:
        book_resp = make_request_using_cache(title[0], "book")

        #Select an edition of the book based on returned results
        if "items" in book_resp.keys(): #Ensures book_resp has returned books, not an error resp
            #Loop through all of the books returned to find the one the referenced in movie list
            for book in book_resp["items"]:
                book_title = book["volumeInfo"]["title"].replace(" ", "-")

                if  title[0] == book_title and "subtitle" not in book["volumeInfo"] and \
                        book_is_found == False:
                    try:
                        book_year = book["volumeInfo"]["publishedDate"]
                    except:
                        book_year = "Unknown"
                    try:
                        book_author = book["volumeInfo"]["authors"][0]
                    except:
                        book_author = "Unknown"
                    try:
                        book_description = book["volumeInfo"]["description"]
                    except:
                        book_description = "None"

                    book_is_found = True

                    #Look up foreign key for movie_id from Movies table
                    statement = "SELECT Id FROM Movies WHERE Title=?"
                    result = cur.execute(statement, (book_title,))
                    for row in result:
                        movie_id = int(row[0])

                    #Insert book into media.db
                    insertion = (None, book_title, book_year, book_author, book_description, movie_id)
                    statement = 'INSERT INTO "Books" '
                    statement += "VALUES (?, ?, ?, ?, ?, ?)"
                    cur.execute(statement, insertion)
                    conn.commit()

            #Reset so that next title in title_list will search for matching book
            book_is_found = False
    conn.close()



#  Query database for all titles of movies in the Bechdel test data set.
#  params:         cur - DB cursor
#          titles_list - the (empty) list of titles
# returns: the list of titles in the data set

def get_bechdel_titles(cur, titles_list):
    #Query Bechdel Stats table to get the list of titles in set of movies
    statement = "SELECT BechdelStats.Title FROM BechdelStats"
    results = cur.execute(statement)
    titles_tuple = results.fetchall()

    #Process title data by converting immutable tuple to mutable list
    for title in titles_tuple:
        titles_list.append(list(title))

    for title in titles_list:
        title[0]=title[0].replace(" ", "-")

    return titles_list



#  Make request or retrieve previous request from cache
#  params:      title - title of the media
#          media_type - string to distinguish book from movie title
# returns: cached data associated with dict entry at that url

def make_request_using_cache(title, media_type):
    if media_type == "movie":
        url = "http://www.omdbapi.com/?apikey=" + secret.OMDB_API_KEY + "&t=" + title
    elif media_type == "book":
        url = "https://www.googleapis.com/books/v1/volumes?q=" + title
    unique_id = url

    ## First, look in the cache to see if we already have this data
    if unique_id in CACHE_DICTION:
        print("Getting cached data from " + unique_id + "...")
        return CACHE_DICTION[unique_id]

    ## If not, fetch the data afresh, add it to the cache,
    ## then write the cache to file.
    print("Making a request for new data from " + url + "...")

    # Make the request and cache the new data
    resp = requests.get(url)
    CACHE_DICTION[unique_id] = json.loads(resp.text)
    dumped_json_cache = json.dumps(CACHE_DICTION)
    fw = open(CACHE_FNAME,"w")
    fw.write(dumped_json_cache)
    fw.close() # Close the open file
    return CACHE_DICTION[unique_id]



# Query the database for movies and books, and create a list of objects
# for each data set based on the returned query result.
#  params:    sortby - column to sort by
#          sortorder - ascending or descending values
# returns: media_list
def search_media_from_db (title=''):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    movie_obj_list = []
    book_obj_list = []
    media_list = []

    #Query database to retrieve all movie records
    statement = "SELECT * FROM Movies WHERE Title LIKE '%{search}%'".format(search=title)
    movie_results = cur.execute(statement)
    movie_results_list = movie_results.fetchall()
    for movie_tuple in movie_results_list:

        #Query database to get the Bechdel test status data for the given movie
        statement = "SELECT BechdelStats.Status FROM BechdelStats JOIN Movies ON Movies.BechdelId=BechdelStats.Id" \
                    " WHERE Movies.BechdelId=" + str(movie_tuple[8])
        stats_results = cur.execute(statement)
        status_results_list = stats_results.fetchall()

        #Add Movie to list of Movie objects
        movie_obj_list.append(Movie(movie_tuple[1], movie_tuple[3], movie_tuple[2], movie_tuple[6],
                                             movie_tuple[4], movie_tuple[5], movie_tuple[7], status_results_list[0][0]))

    #Query database to retrieve all book records and add Book to list of Book objects
    statement = "SELECT * FROM Books WHERE Title LIKE '%{search}%'".format(search=title)
    book_results = cur.execute(statement)
    book_results_list = book_results.fetchall()
    for book_tuple in book_results_list:
        book_obj_list.append(Book(book_tuple[1], book_tuple[3], book_tuple[2], book_tuple[4]))

    conn.close()

    #Combine both media objects into a single list
    for book in book_obj_list:
        media_list.append(["book", book.title, book.author, book.year[:4], book.summary, "", "", "UNKNOWN"])
    for movie in movie_obj_list:
        media_list.append(["movie", movie.title, movie.author, movie.year, movie.summary, movie.rating, movie.genres,
                           movie.status])

    sort_col = 1

    media_list.sort(key=lambda row: row[sort_col], reverse=False)

    return media_list

def get_media_from_db (sortby='Title', sortorder='desc'):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    movie_obj_list = []
    book_obj_list = []
    media_list = []

    #Query database to retrieve all movie records
    statement = "SELECT * FROM Movies"
    movie_results = cur.execute(statement)
    movie_results_list = movie_results.fetchall()
    for movie_tuple in movie_results_list:

        #Query database to get the Bechdel test status data for the given movie
        statement = "SELECT BechdelStats.Status FROM BechdelStats JOIN Movies ON Movies.BechdelId=BechdelStats.Id" \
                    " WHERE Movies.BechdelId=" + str(movie_tuple[8])
        stats_results = cur.execute(statement)
        status_results_list = stats_results.fetchall()

        #Add Movie to list of Movie objects
        movie_obj_list.append(Movie(movie_tuple[1], movie_tuple[3], movie_tuple[2], movie_tuple[6],
                                             movie_tuple[4], movie_tuple[5], movie_tuple[7], status_results_list[0][0]))

    #Query database to retrieve all book records and add Book to list of Book objects
    statement = "SELECT * FROM Books"
    book_results = cur.execute(statement)
    book_results_list = book_results.fetchall()
    for book_tuple in book_results_list:
        book_obj_list.append(Book(book_tuple[1], book_tuple[3], book_tuple[2], book_tuple[4]))

    conn.close()

    #Combine both media objects into a single list
    for book in book_obj_list:
        media_list.append(["book", book.title, book.author, book.year[:4], book.summary, "", "", "UNKNOWN"])
    for movie in movie_obj_list:
        media_list.append(["movie", movie.title, movie.author, movie.year, movie.summary, movie.rating, movie.genres,
                           movie.status])

    #Define how to sort the media list
    if sortby == 'type':
        sort_col = 0
    elif sortby == 'title':
        sort_col = 1
    elif sortby == 'author':
        sort_col = 2
    elif sortby == 'status':
        sort_col = 7
    else:
        sort_col = 1

    rev = (sortorder == 'desc')
    media_list.sort(key=lambda row: row[sort_col], reverse=rev)

    return media_list

if __name__ == "__main__":
    init_db()
    insert_bechdel_stats_into_db()
    insert_movies_into_db()
    insert_books_into_db()