from flask import Flask, render_template, request

from openai import OpenAI

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

@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    imt = None
    calories = None
    advice = None
    ai_plan = None

    if request.method == 'POST':
        weight = float(request.form['weight'])
        height_cm = float(request.form['height'])
        height = height_cm / 100
        activity = int(request.form['activity'])
        goal = request.form['goal']

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

        try:
            client = OpenAI(
                base_url="https://text.pollinations.ai/openai",
                api_key="no_key_needed",
            )

            prompt = (
                f"Ты профессиональный фитнес-тренер. Составь краткий план тренировок на неделю "
                f"для человека с ИМТ {imt}, целью '{goal}' и дневной нормой {calories} ккал. "
                f"Если ИМТ меньше 18.5, а цель похудеть, вежливо предупреди, что это опасно и предложи план по набору"
                f"Ответь 3-4 предложениями, без лишних вступлений, на русском"
            )

            response = client.chat.completions.create(
                model="openai",
                messages=[{"role": "user", "content": prompt}],
            )
            ai_plan = response.choices[0].message.content

        except Exception as e:
            print(f"Ошибка ИИ: {e}")
            ai_plan = f"Ошибка ИИ: {e}"

    return render_template('calculators.html', imt=imt, calories=calories, advice=advice, ai_plan=ai_plan)

app.run(debug=True)