import uuid

from flask import redirect, render_template, request, url_for
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash


PLANS = {
    "month": {"name": "Пробный", "price": 10_000, "duration": "1 месяц"},
    "six_months": {"name": "Будь в форме", "price": 50_000, "duration": "6 месяцев"},
    "year": {"name": "Максимум возможностей", "price": 100_000, "duration": "1 год"},
}


def register_routes(app, db, client_model):
    """Register the application's HTTP routes on its Flask app."""

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

    @app.route("/calculators", methods=["GET", "POST"])
    def calculator():
        imt = None
        calories = None
        advice = None

        if request.method == "POST":
            weight = float(request.form["weight"])
            height = float(request.form["height"]) / 100
            activity = int(request.form["activity"])

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

        return render_template(
            "calculators.html", imt=imt, calories=calories, advice=advice
        )

    @app.route("/account_click")
    def account_click():
        if current_user.is_authenticated:
            return redirect(url_for("personal_ac"))
        return redirect(url_for("register"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("personal_ac"))

        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")
            gender = request.form.get("gender")

            user_exists = client_model.query.filter_by(email=email).first()
            if user_exists:
                return "Этот Email уже занят!"

            new_client = client_model(
                id=str(uuid.uuid4()),
                name=name,
                email=email,
                password=generate_password_hash(password),
                gender=gender,
            )
            db.session.add(new_client)
            db.session.commit()
            login_user(new_client)
            return redirect(url_for("personal_ac"))

        return render_template("registration.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("personal_ac"))

        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            client = client_model.query.filter_by(email=email).first()

            if client and check_password_hash(client.password, password):
                login_user(client)
                return redirect(url_for("personal_ac"))
            return "Неверный email или пароль"

        return render_template("auth.html")

    @app.route("/personal_ac")
    @login_required
    def personal_ac():
        return render_template("personal_ac.html", current_user=current_user)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

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
