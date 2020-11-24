#################################
##### Name: Zitong Liao
##### Uniqname: liaozt
#################################
from flask import Flask, render_template, url_for, request
import final_project_setup as setup
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/Bechdel')
def Bechdel():
    return render_template('Bechdel.html')

@app.route('/search', methods=['GET', 'POST'])
def Search():
    if request.method == 'POST':
        title = request.form['title']
        media_list = setup.search_media_from_db(title)
    else:
        media_list = setup.search_media_from_db()
    return render_template('search.html', media_list= media_list)

@app.route('/chart', methods=['GET', 'POST'])
def chart():
    if request.method == 'POST':
        sortby = request.form['sortby']
        if "sortorder" in request.form.keys():
            sortorder = request.form['sortorder']
        else:
            sortorder = "asc"
        media_list = setup.get_media_from_db(sortby, sortorder)
    else:
        media_list = setup.get_media_from_db()
    return render_template('chart.html', media_list=media_list)




if __name__ == '__main__':

    if len(sys.argv) > 1 and sys.argv[1] == '--init':
        setup.init_db()
        setup.insert_bechdel_stats_into_db()
        setup.insert_movies_into_db()
        setup.insert_books_into_db()

    print('Starting Flask app...', app.name)
    app.run(debug=True)