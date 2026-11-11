from datetime import datetime, timedelta, timezone

from flask import Flask
from sqlalchemy import inspect, text
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
login_manager.login_view = 'register'


class Client(db.Model, UserMixin):
    __tablename__ = 'client'

    id = db.Column(db.String(120), unique=True, nullable=False, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    gender = db.Column(db.String(7), nullable=False)
    client = db.relationship('Client', backref='payments')


class Pay(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.Integer, primary_key=True)
    id_client = db.Column(db.String(120), db.ForeignKey('client.id'), nullable=False)
    abonent_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    summa = db.Column(db.Integer, nullable=False)
    tarif = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Не оплачено')
    # Store UTC without an offset because SQLite DateTime does not retain it.
    created_at = db.Column(db.DateTime, nullable=True,
                           default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    @property
    def purchased_at_moscow(self):
        if self.created_at is None:
            return None
        return self.created_at.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=3)))


class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    __table_args__ = (db.CheckConstraint('price > 0', name='product_positive_price'),)


class ProductPurchase(db.Model):
    __tablename__ = 'product_purchase'

    payment_id = db.Column(db.String(120), db.ForeignKey('payment.id'), primary_key=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product')
    payment = db.relationship('Pay')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    


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

register_routes(app, db, Client, Trener, Product, Pay, ProductPurchase)


def upgrade_payment_timestamps(engine=None):
    """Extend existing SQLite databases without inventing dates for old payments."""
    engine = engine if engine is not None else db.engine
    inspector = inspect(engine)
    if inspector.has_table('payment') and 'created_at' not in {
        column['name'] for column in inspector.get_columns('payment')
    }:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE payment ADD COLUMN created_at DATETIME'))


@app.cli.command('upgrade-purchases')
def upgrade_purchases_command():
    """Add purchase timestamps to an existing database."""
    upgrade_payment_timestamps()
    print('Purchase timestamps are ready.')


def init_shop():
    """Add shop tables and missing starter items without changing existing data."""
    from shop_catalog import PRODUCTS

    upgrade_payment_timestamps()
    db.metadata.create_all(db.engine, tables=[Product.__table__, ProductPurchase.__table__])
    for item in PRODUCTS:
        if db.session.get(Product, item['id']) is None:
            db.session.add(Product(**item))
    db.session.commit()


@app.cli.command('init-shop')
def init_shop_command():
    """Initialize the shop in an existing application database."""
    init_shop()
    print('Магазин готов: таблицы созданы, товары добавлены.')
register_routes(app, db, Client, Trener, Pay)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_shop()

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