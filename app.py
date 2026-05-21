from flask import Flask, render_template, request, jsonify, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os

app = Flask(__name__)
app.secret_key = "babilon_secure_core"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///babilon.db"
db = SQLAlchemy(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(200))


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    message = db.Column(db.Text)
    response = db.Column(db.Text)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":

        user = User.query.filter_by(
            username=request.form["username"]
        ).first()

        if user and check_password_hash(
            user.password,
            request.form["password"]
        ):
            session["user"] = user.id
            return redirect("/")

    return render_template("login.html")


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        new_user = User(
            username=request.form["username"],
            password=generate_password_hash(
                request.form["password"]
            )
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/chat", methods=["POST"])
def chat():

    msg = request.json["message"]

    history = Chat.query.filter_by(
        user_id=session["user"]
    ).order_by(Chat.id.desc()).limit(8).all()

    memory=[]

    for h in reversed(history):
        memory.append({"role":"user","content":h.message})
        memory.append({"role":"assistant","content":h.response})

    payload = {
        "model":"llama-3.1-8b-instant",
        "messages":[
            {
                "role":"system",
                "content":"""
You are Babilon AI.

Created by Samohgee.

You are futuristic, scientific, elite, intelligent and concise.

You remember previous conversations.

Never call yourself a generic language model.
Always identify as Babilon AI created by Samohgee.

If web information is requested, provide updated live-style answers.
"""
            }
        ] + memory + [
            {
                "role":"user",
                "content":msg
            }
        ]
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization":f"Bearer {GROQ_API_KEY}",
            "Content-Type":"application/json"
        },
        json=payload
    )

    result=response.json()

    reply=result["choices"][0]["message"]["content"]

    chatlog=Chat(
        user_id=session["user"],
        message=msg,
        response=reply
    )

    db.session.add(chatlog)
    db.session.commit()

    return jsonify({"response":reply})


@app.route("/admin")
def admin():
    users=User.query.all()
    chats=Chat.query.all()
    return render_template("admin.html",users=users,chats=chats)


if __name__=="__main__":
    app.run(debug=True)
