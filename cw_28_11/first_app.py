from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.get("/")
def index():
    return "Hello, world!"

@app.get("/items")
def items():
    data = [
        {"title": "anya", "desc": "очень умная студентка"},
        {"title": "bulat", "desc": "любит backend"},
        {"title": "hello", "desc": "слово-приветствие"}
    ]
    return render_template("items.html", items=data)

@app.get("/user/<name>")
def user(name):
    return render_template("user.html", name=name)

@app.get("/search")
def search():
    username = request.args.get("username")
    if username:
        return redirect(url_for("user", name=username))
    return render_template("search.html")

@app.get("/about")
def about():
    return render_template("about.html")

if __name__ == '__main__':
    app.run(debug=True)