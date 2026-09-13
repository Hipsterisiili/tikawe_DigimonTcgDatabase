import random

from flask import Flask
import db
from flask import redirect, render_template, request
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    result = db.query("SELECT COUNT(*) FROM cards")
    count = result[0][0]
    return "Kortteja on tietokannassa yhteensä " + str(count) + " kappaletta"


@app.route("/cards")
def cards():

    cardAmount = db.query("SELECT COUNT(*) FROM cards")
    cardList = db.query("SELECT name FROM cards")
    latestCard = db.query("SELECT name FROM cards ORDER BY id DESC LIMIT 1")

    return render_template("cards.html", count = cardAmount[0][0], cardList = cardList, latest_card = latestCard[0][0])


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

@app.route("/randomcard")
def randomCard():
    addRandomCard()
    return redirect("/cards")

def addRandomCard():
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
    
    db.execute(
        "INSERT INTO cards (name) VALUES (?)",
        (randomCardName,)
    )

@app.route("/deletecard")
def deletecard():
    db.execute(
            "DELETE FROM cards WHERE id = (SELECT MAX(id) FROM cards)"
        )
    return redirect("/cards")
