import uuid
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# Импортируем необходимые инструменты для авторизации
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# Импортируем безопасное хэширование паролей
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Секретный ключ ОБЯЗАТЕЛЕН для работы сессий и Flask-Login!
app.config['SECRET_KEY'] = 'your-very-secure-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soprano.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Настраиваем Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Перенаправит сюда, если неавторизованный полезет в ЛК


# Чтобы класс Client работал с Flask-Login, добавляем ему родителя UserMixin
class Client(db.Model, UserMixin):
    __tablename__ = 'client'

    # Так как id строковый, при регистрации будем генерировать уникальный UUID строкой
    id = db.Column(db.String(120), unique=True, nullable=False, primary_key=True)
    password = db.Column(db.String(255), nullable=False)  # Изменил Integer на String для хэша пароля
    name = db.Column(db.String(50), nullable=False)
    # Почта должна быть уникальной, и на неё ссылается внешний ключ
    email = db.Column(db.String(255), unique=True, nullable=False)
    gender = db.Column(db.String(7), nullable=False)


class Pay(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.String(120), unique=True, nullable=False, primary_key=True)
    email = db.Column(db.String(120), db.ForeignKey('client.email'), nullable=False)
    payment = db.Column(db.Boolean, default=False, nullable=False)


# Функция для Flask-Login, которая загружает пользователя из БД по его ID из сессии
@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(user_id)


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


# Кнопка "Личный кабинет" на главной должна вести на этот роут:
@app.route('/account_click')
def account_click():
    if current_user.is_authenticated:
        return redirect(url_for('personal_ac'))
    else:
        return redirect(url_for('register'))


# РЕГИСТРАЦИЯ: принимает и GET (показ формы) и POST (отправка данных формы)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('personal_ac'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        gender = request.form.get('gender')

        # Проверяем, нет ли уже такого пользователя
        user_exists = Client.query.filter_by(email=email).first()
        if user_exists:
            return "Этот Email уже занят!"  # Для простоты выводим текст, потом можно сделать красивее

        # Генерируем уникальный текстовый ID и хэшируем пароль
        user_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)

        new_client = Client(id=user_id, name=name, email=email, password=hashed_password, gender=gender)

        db.session.add(new_client)
        db.session.commit()

        # Автоматически авторизуем пользователя сразу после регистрации
        login_user(new_client)

        # Перенаправляем в личный кабинет
        return redirect(url_for('personal_ac'))

    return render_template('registration.html')


# АВТОРИЗАЦИЯ: вход для тех, кто уже зарегистрирован
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('personal_ac'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        client = Client.query.filter_by(email=email).first()

    # Проверяем пароль с помощью check_password_hash
        if client and check_password_hash(client.password, password):
            login_user(client)  # Записываем в сессию
            return redirect(url_for('personal_ac'))
        else:
            return "Неверный email или пароль"

    return render_template('auth.html')


# ЛИЧНЫЙ КАБИНЕТ: доступен только вошедшим пользователям
@app.route("/personal_ac")
@login_required  # Flask-Login сам выгонит отсюда, если юзер не залогинен
def personal_ac():
    # current_user будет автоматически доступен в шаблоне,
    # но мы можем передать его явно, как у вас и было.
    return render_template("personal_ac.html", current_user=current_user)





if __name__ == '__main__':
    app.run(debug=True)