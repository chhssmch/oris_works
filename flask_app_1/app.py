from flask import Flask, render_template, request, redirect, url_for
import random

app = Flask(__name__)

quotes = [
    "Волк меняет шерсть, а не натуру",
    "Вытри слёзы, ведь волки не плачут, не к лицу им притворяться людьми",
    "У волков нет правил поведения. Волкам, чтобы быть волками, не нужны никакие правила",
    "Жизнь волка не легка, а жизнь человека запутана",
    "Волк никогда не будет жить в загоне, но загоны всегда будут жить в волке",
    "Лучше быть тем кем есть, чем быть тем, кем не будешь",
    "Чтобы не искать выход, посмотри внимательно на вход" ]

images = ["corn.jpeg", "flower.jpeg", "lolipop.jpeg", "marryme.jpeg",
          "meditation.jpeg", "glasses.jpeg", "egg.jpeg", "hat.jpeg"]

movies = [
    {"title": "Гарри Поттер и философский камень", "year": 2001, "rating": 7.6},
    {"title": "Гарри Поттер и тайная комната", "year": 2002, "rating": 7.4},
    {"title": "Гарри Поттер и узник Азкабана", "year": 2004, "rating": 7.9},
    {"title": "Гарри Поттер и кубок огня", "year": 2005, "rating": 7.7},
    {"title": "Гарри Поттер и орден Феникса", "year": 2007, "rating": 7.5},
    {"title": "Гарри Поттер и принц-полукровка", "year": 2009, "rating": 7.6},
    {"title": "Гарри Поттер и дары смерти: Часть 1", "year": 2010, "rating": 7.7},
    {"title": "Гарри Поттер и дары смерти: Часть 2", "year": 2011, "rating": 8.1} ]

@app.get("/quote")
def quote():
    random_quote = random.choice(quotes)
    return render_template('quote.html', quote=random_quote)

@app.get("/gallery")
def gallery():
    return render_template('gallery.html', images=images)

@app.route('/movies')
def movies_page():
    return render_template('movies.html', movies=movies)

@app.route('/calc', methods=['GET'])
def calc():
    result = None
    error = None
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    op = request.args.get('op')

    if (a is not None and b is not None and op):
        try:
            if op == '+':
                result = a + b
            elif op == '-':
                result = a - b
            elif op == '*':
                result = a * b
            elif op == '/':
                if b == 0:
                    error = "Ошибка! Деление на ноль"
                else:
                    result = a / b
        except:
            error = "Ошибка вычисления"

    return render_template('calc.html', result=result, error=error, a=a, b=b, op=op)


@app.route('/convert', methods=['GET'])
def convert():
    result = None
    value = request.args.get('value', type=float)
    direction = request.args.get('direction')

    if value is not None and direction:
        if direction == 'c_to_f':
            converted = value * 9 / 5 + 32
            result = f"{value}°C = {converted:.1f}°F"
        elif direction == 'f_to_c':
            converted = (value - 32) * 5 / 9
            result = f"{value}°F = {converted:.1f}°C"

    return render_template('convert.html', result=result, value=value, direction=direction)

if __name__ == '__main__':
    app.run(debug=True)
