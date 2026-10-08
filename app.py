import uuid
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

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

@app.route('/calculators', methods=['GET', 'POST'])
def calculator():
    imt = None
    calories = None
    advice = None

    if request.method == 'POST':
        weight = float(request.form['weight'])
        height = float(request.form['height']) / 100
        activity = int(request.form['activity'])

        imt = round(weight / (height * height), 2)
        calories = round(weight * activity)

        if imt < 18.5:
            advice = "У вас недостаток веса. Рекомендуем набрать массу."
        elif imt < 25:
            advice = "У вас нормальный вес. Так держать!"
        elif imt < 30:
            advice = "У вас избыточный вес. Рекомендуем похудеть."
        else:
            advice = "У вас ожирение. Рекомендуем обратиться к врачу."

    return render_template('calculators.html', imt=imt, calories=calories, advice=advice)


@app.route('/account_click')
def account_click():
    if current_user.is_authenticated:
        return redirect(url_for('personal_ac'))
    else:
        return redirect(url_for('register'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('personal_ac'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        gender = request.form.get('gender')


        user_exists = Client.query.filter_by(email=email).first()
        if user_exists:
            return "Этот Email уже занят!"


        user_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)

        new_client = Client(id=user_id, name=name, email=email, password=hashed_password, gender=gender)

        db.session.add(new_client)
        db.session.commit()


        login_user(new_client)


        return redirect(url_for('personal_ac'))

    return render_template('registration.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('personal_ac'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        client = Client.query.filter_by(email=email).first()


        if client and check_password_hash(client.password, password):
            login_user(client)  # Записываем в сессию
            return redirect(url_for('personal_ac'))
        else:
            return "Неверный email или пароль"

    return render_template('auth.html')



@app.route("/personal_ac")
@login_required
def personal_ac():


    return render_template("personal_ac.html", current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

PLANS = {
    "month": {"name": "Пробный", "price": 10_000, "duration": "1 месяц"},
    "six_months": {"name": "Будь в форме", "price": 50_000, "duration": "6 месяцев"},
    "year": {"name": "Максимум возможностей", "price": 100_000, "duration": "1 год"},
}

@app.route("/payment/<plan_id>")
@login_required
def payment_page(plan_id):
    plan = PLANS.get(plan_id)
    if plan is None:
        return "Абонемент не найден", 404

    return render_template("payment.html", plan=plan)

@app.route("/payment_success.html", methods=["GET", "POST"])
def payment_success():
    return render_template("payment_success.html")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
