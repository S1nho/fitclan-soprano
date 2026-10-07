from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import current_user

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soprano.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Client(db.Model):
    __tablename__ = 'client'

    id = db.Column(db.String(120), unique = True, nullable = False, primary_key = True)
    password = db.Column(db.Integer, nullable = False)
    name = db.Column(db.String(50), nullable = False)
    email = db.Column(db.String(255), nullable = False)
    gender = db.Column(db.String(7), nullable = False)

class Pay(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.String(120), unique = True, nullable = False, primary_key = True)
    email = db.Column(db.String(120), db.ForeignKey('client.email'), nullable = False)
    payment = db.Column(db.Boolean, default = False, nullable = False)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/abonements")
def abonements():
    return render_template("abonements.html")

@app.route("/directions")
def directions():
    return render_template("directions.html")

@app.route("/trainers")
def trainers():
    return render_template("trainers.html")

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")

@app.route('/register')
def register():

    return render_template('registration.html')

@app.route('/login')
def login():

    return render_template('auth.html')

@app.route("/personal_ac")

def personal_ac():
    return render_template("personal_ac.html", current_user=current_user)

if __name__ == '__main__':
    app.run(debug=True)