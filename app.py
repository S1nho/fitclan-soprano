from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soprano.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Client(db.Model):
    __tablename__ = 'client'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(255), nullable = False)

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

app.run(debug=True)