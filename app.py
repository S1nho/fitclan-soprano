from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin

app = Flask(__name__)


app.config['SECRET_KEY'] = 'your-very-secure-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soprano.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


login_manager = LoginManager(app)
login_manager.login_view = 'login'



class Client(db.Model, UserMixin):
    __tablename__ = 'client'


    id = db.Column(db.String(120), unique=True, nullable=False, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(50), nullable=False)

    email = db.Column(db.String(255), unique=True, nullable=False)
    gender = db.Column(db.String(7), nullable=False)


class Pay(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.String(120), unique=True, nullable=False, primary_key=True)
    email = db.Column(db.String(120), db.ForeignKey('client.email'), nullable=False)
    payment = db.Column(db.Boolean, default=False, nullable=False)
    summa = db.Column(db.Integer, nullable=False)
    tarif = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Не оплачено')




@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(user_id)

from routes import register_routes

register_routes(app, db, Client)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
