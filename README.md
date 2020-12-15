## Bechdel test App
A software to see if your favorite movie has a book of the same name and if it passes the Bechdel test.

### Prerequisites

Python3, Flask, sqlite3, requests

### Demo video

https://drive.google.com/file/d/1cjZx5buMjKwDghbyuay_LKn4g7dwCi2a/view?usp=sharing

### Configure the project

Please follow these steps:

1. Clone the repository onto your local system.
```
$ git clone https://github.com/liaozter/Final-Project.git
```

2. The construction of the database takes quite a few minutes according to the network speed. Therefore, for the convenience of grading, I provide a full database and cache files. If you don't need to update the data and have the following files, then you can go to the next section and open the app.
    1. media_cache.json
    2. media.db

3. If you want to initiate the database and lose the file media_cache.json, then go to http://www.omdbapi.com/apikey.aspx and get API keys as instruction. I provide my API KEY in the Final Project Submission on CANVAS.
   Open the secret.py file and and fill in your API keys.
   Run final_project_setup.py by :
```
$ python final_project_setup.py
```

## Running the application
1. Run "final_project_app.py" file
```
$ python final_project_app.py
```

If you wants to renew the database, try:
```
$ python3 final_project_app.py --init
```
2. Navigate to "http://127.0.0.1:5000/" by clicking or copy it in a web browser.

3. Navigate to other pages by clicking.
Three Pages in total:
    1. What is the Bechdel test: Show the overview of the Bechdel test
    2. Find your favorite movie or book: Search for movies or books that the user wants to check
    3. Sort all movies and books:A chart allows user sort the book and movies by Type, Title, Author or Bechdel test result. (Ascending or Descending)

4. Use ctrl + c to end the app.