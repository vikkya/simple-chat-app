# Simple Chat App

### Tech Stack
* Flask
* Flask-Login
* Flask-Socketio
* Bootstrap
* Gunicorn
* Heroku

###### How to run the application
* clone the repo
* create a virtual env - *python -m venv chat*
* activate the venv - *chat\Scripts\activate* - windows only
* open a terminal in same location as cloned
* run *python3 app.py* if you have any error follow below steps and run it again

###### Change *SECRET_KEY*, *DATABASE_URL*, *DB_NAME*
* SECRET_KEY - app.py file line number 11
* DATABASE_URL - db.py - line number 8
* DB_NAME -db.py - line number 10

### How to use
* signup or login with *admin/admin* 
* create groups, invite users, edit group

Application is hosted on Heroku.

[Click-Here](https://vikky-simple-chat-app.herokuapp.com/)