from flask import Flask, render_template, request

app = Flask(__name__)

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

app.run(debug=True)