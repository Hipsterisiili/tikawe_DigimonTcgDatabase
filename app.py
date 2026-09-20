"""
Main application file
"""
import random
import sqlite3
from flask import Flask, redirect, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import db
import secrets

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)  # This gives you a 16-byte random URL-safe token
username = ""
private_table_name = ""

def update_name(word):
    username = word
    private_table_name = username.replace(" ", "_").replace("-", "_")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/full_card_list")
def full_card_list():
    card_amount = db.query("SELECT COUNT(*) FROM cards")
    card_list = db.query("SELECT name FROM cards")
    latest_card = db.query("SELECT name FROM cards ORDER BY id DESC LIMIT 1")
    
    return render_template(
        "full_card_list.html",
        username = username,
        count = card_amount[0][0],
        card_list = card_list,
        latest_card = latest_card[0][0])

@app.route("/personal_card_list")
def personal_card_list():
    private_table_name = session["username"]
    card_amount_result = db.query(f"SELECT COUNT(*) FROM `{private_table_name}`")
    card_amount = card_amount_result[0][0] if card_amount_result else 0 
    card_list = db.query(f"SELECT id, name FROM `{private_table_name}`")
    latest_card_result = db.query(f"SELECT name FROM `{private_table_name}` ORDER BY id DESC LIMIT 1")
    latest_card = latest_card_result[0][0] if latest_card_result else None
    if card_amount == 0:
        return "Tietokantasi on tyhjä"
    else:
        return render_template(
                "personal_card_list.html", 
            count = card_amount[0][0],
            card_list = card_list,
            latest_card = latest_card[0][0])

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
    
    try:
        db.execute(f"CREATE TABLE IF NOT EXISTS `{username}` (id INTEGER PRIMARY KEY, name TEXT)")
    except Exception as e:
        return f"Virhe käyttäjän taulun luomisessa: {str(e)}"
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    sql = "SELECT password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])
    if len(result) == 0:
        return "VIRHE: käyttäjätunnusta ei löydy"
    stored_hash = result[0]["password_hash"]
    if not check_password_hash(stored_hash, password):
        return "VIRHE: väärä salasana"
    session["username"] = username    
    update_name(username)
    return redirect("/")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

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
    return redirect("/")

@app.route("/random_card")
def random_card():
    add_random_card()
    return redirect("/")

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
    return redirect("/")
