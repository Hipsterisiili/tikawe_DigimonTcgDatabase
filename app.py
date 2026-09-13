"""
Main application file
"""
import random

from flask import Flask, redirect, render_template, request
import db
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    result = db.query("SELECT COUNT(*) FROM cards")
    count = result[0][0]
    return "Kortteja on tietokannassa yhteensä " + str(count) + " kappaletta"

@app.route("/cards")
def cards():

    card_amount = db.query("SELECT COUNT(*) FROM cards")
    card_list = db.query("SELECT name FROM cards")
    latest_card = db.query("SELECT name FROM cards ORDER BY id DESC LIMIT 1")

    return render_template(
        "cards.html", 
        count = card_amount[0][0],
        card_list = card_list,
        latest_card = latest_card[0][0])

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

@app.route("/random_card")
def random_card():
    add_random_card()
    return redirect("/cards")

def add_random_card():
    card_names = [
            "Agumon",
            "Gabumon",
            "Patamon",
            "Gatomon",
            "Tentomon",
            "Palmon",
            "Gomamon",
            "Biyomon"
        ]

    random_card_name = random.choice(card_names)

    db.execute(
        "INSERT INTO cards (name) VALUES (?)",
        (random_card_name,)
    )

@app.route("/delete_card")
def delete_card():
    db.execute(
            "DELETE FROM cards WHERE id = (SELECT MAX(id) FROM cards)"
        )
    return redirect("/cards")
