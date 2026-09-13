import random

from flask import Flask
from flask import redirect, render_template, request
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    db = sqlite3.connect("database.db")
    db.execute("INSERT INTO visits (visited_at) VALUES (datetime('now'))")
    db.commit()
    result = db.execute("SELECT COUNT(*) FROM visits").fetchone()
    count = result[0]
    db.close()
    return "Sivua on ladattu " + str(count) + " kertaa"


@app.route("/cards")
def cards():
    cardnames = [
        "Agumon",
        "Gabumon",
        "Patamon",
        "Gatomon",
        "Tentomon",
        "Palmon",
        "Gomamon",
        "Biyomon"
    ]

    randomCardName = random.choice(cardnames)

    db = sqlite3.connect("database.db")

    db.execute(
        "INSERT INTO cards (name) VALUES (?)",
        (randomCardName,)
    )
    db.commit()

    cardAmount = db.execute("SELECT COUNT(*) FROM cards").fetchone()
    cardList = db.execute("SELECT name FROM cards").fetchall()
    latestCard = db.execute("SELECT name FROM cards ORDER BY id DESC LIMIT 1").fetchone()

    db.close()

    return render_template("cards.html", count = cardAmount[0], cardList = cardList, latest_card = latestCard[0])


@app.route("/newcard")
def new():
    return render_template("newcard.html")


@app.route("/send", methods=["POST"])
def send():
    content = request.form["content"]
    db = sqlite3.connect("database.db")
    db.execute("INSERT INTO cards (name) VALUES (?)", (content,))
    db.commit()
    db.close()
    return redirect("/cards")