"""
Main application file
"""
import random

from flask import Flask, redirect, render_template, request
from werkzeug.security import generate_password_hash
import db
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    result = db.query("SELECT COUNT(*) FROM cards")
    count = result[0][0]
    return "Kortteja on tietokannassa yhteensä " + str(count) + " kappaletta"

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return "VIRHE: salasanat eivät ole samat"
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "VIRHE: tunnus on jo varattu"

    return "Tunnus luotu"



@app.route("/login")
def login():
    return render_template("login.html")



def check_password_hash(stored_hash, password):
    # This is a placeholder for password hash checking logic.
    # In a real application, you should use a secure hashing algorithm.
    return stored_hash == "hashed_" + password


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
