from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin
from datetime import datetime
from openai import OpenAI

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

    id = db.Column(db.Integer, primary_key=True)
    id_client = db.Column(db.String(120), db.ForeignKey('client.id'), nullable=False)
    abonent_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    summa = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship('Client', backref='payments')


class Trener(db.Model, UserMixin):
    __tablename__ = "trainers"

    id_trainers = db.Column(db.String(120), primary_key=True)
    name_trainer = db.Column(db.String(50), nullable=False)
    email_trainer = db.Column(db.String(255), unique=True, nullable=False)
    password_trainers = db.Column(db.String(255), nullable=False)
    id_direction = db.Column(db.Integer, db.ForeignKey('direction.id_direction'), nullable=False)
    direction = db.relationship('Direction', backref='trainers')


class Direction(db.Model):
    __tablename__ = "direction"

    id_direction = db.Column(db.Integer, primary_key=True)
    name_direction = db.Column(db.String(100), unique=True, nullable=False)


class Abonent(db.Model):
    __tablename__ = 'abonent'

    id_abonent = db.Column(db.Integer, primary_key=True, unique=True)
    name_abonent = db.Column(db.String(50), nullable=False)



@login_manager.user_loader
def load_user(user_id):
    trainer = Trener.query.filter_by(id_trainers=user_id).first()
    if trainer:
        trainer.get_id = lambda: str(trainer.id_trainers)
        return trainer

    return Client.query.get(user_id)


from routes import register_routes

register_routes(app, db, Client, Trener, Pay)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not Client.query.first():
            from werkzeug.security import generate_password_hash
            db.session.add_all([
                Client(
                    id="kapitalina", 
                    name="Капиталина", 
                    email="kapa@mail.ru", 
                    password=generate_password_hash("viper6752"),
                    gender="Женский"
                ),
                Client(
                    id="leonid", 
                    name="Леонид", 
                    email="leo@mail.ru", 
                    password=generate_password_hash("loenid1978"),
                    gender="Мужской"
                ),
                Client(
                    id="yura",
                    name="Юра",
                    email="lada@gmail.com",
                    password=generate_password_hash("lada10777"),
                    gender="Мужской"
                )
            ])
            db.session.commit()

        if not Direction.query.first():
            db.session.add_all([
                Direction(id_direction=1, name_direction='Силовая'),
                Direction(id_direction=2, name_direction='Бокс'),
                Direction(id_direction=3, name_direction='Йога'),
                Direction(id_direction=4, name_direction='Плавание')
            ])
            db.session.commit()

        if not Trener.query.first():
            db.session.add_all([
                Trener(
                    id_trainers="trainer_silovaya", 
                    name_trainer="Максим", 
                    email_trainer="maks@studio.ru", 
                    password_trainers="maks123456",
                    id_direction=1
                ),
                Trener(
                    id_trainers="trainer_box", 
                    name_trainer="Владимир", 
                    email_trainer="box@studio.ru", 
                    password_trainers="box123456", 
                    id_direction=2
                ),
                Trener(
                    id_trainers="trainer_yoga", 
                    name_trainer="Ксения", 
                    email_trainer="yoga@studio.ru", 
                    password_trainers="yoga123456", 
                    id_direction=3
                ),
                Trener(
                    id_trainers="trainer_swim", 
                    name_trainer="Екатерина", 
                    email_trainer="swim@studio.ru", 
                    password_trainers="swim123456", 
                    id_direction=4
                )
            ])
            db.session.commit()

        if not Abonent.query.first():
            db.session.add_all([
                Abonent(
                    id_abonent=1,
                    name_abonent="Попробовать"
                ),
                Abonent(
                    id_abonent=2,
                    name_abonent="Похудеть к лету"
                ),
                Abonent(
                    id_abonent=3,
                    name_abonent="Стать спортсменом"
                )
            ])
            db.session.commit()

        if not Pay.query.first():
            db.session.add_all([
                Pay(
                    id_client="kapitalina",
                    abonent_name="Попробовать",
                    duration="1 месяц",
                    summa=1000
                ),
                Pay(
                    id_client="leonid",
                    abonent_name="Похудеть к лету",
                    duration="3 месяца",
                    summa=3000
                ),
                Pay(
                    id_client="yura",
                    abonent_name="Стать спортсменом",
                    duration="6 месяцев",
                    summa=6000
                )
            ])
            db.session.commit()
            
    app.run(debug=True)