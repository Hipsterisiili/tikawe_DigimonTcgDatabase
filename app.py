"""
Main application file
"""
import random
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, url_for
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


"""
Front page of the app containing: 
- info on whether the user is logged in or not
- link to the global collection
- link to the private collection if logged in
"""
@app.route("/")
def index():
    return render_template("index.html")

"""
This page displays the global collection.
User may:
- Add either specific or random cards to the global collection
- Delete cards from global collection
"""
@app.route("/full_card_list")
def full_card_list():
    card_amount_result = db.query("SELECT COUNT(*) FROM cards")
    card_amount = card_amount_result[0][0] if card_amount_result else 0
    card_list = db.query("SELECT id, name FROM cards")
    latest_card_result = db.query("SELECT name FROM cards ORDER BY id DESC LIMIT 1")
    latest_card = latest_card_result[0][0] if latest_card_result else None
    
    return render_template(
        "full_card_list.html",
        count=card_amount,
        card_list=card_list,
        latest_card=latest_card
    )

"""
This page displays the user's own collection.
User may:
- Add specific or random cards to their own collection
- Delete cards from thwir own collection
"""
@app.route("/personal_card_list")
def personal_card_list():
    private_table_name = session["username"]
    
    card_amount_result = db.query(f"SELECT COUNT(*) FROM `{private_table_name}`")
    card_amount = card_amount_result[0][0] if card_amount_result else 0 
    card_list = db.query(f"SELECT id, name FROM `{private_table_name}`")
    
    latest_card_result = db.query(f"SELECT name FROM `{private_table_name}` ORDER BY id DESC LIMIT 1")
    latest_card = latest_card_result[0][0] if latest_card_result else None

    if(session["username"]):
        target = "private"
    else:
        target = "global"
        

    return render_template(
        "personal_card_list.html", 
        count=card_amount,
        card_list=card_list,
        latest_card=latest_card
    )

"""
Page for creating a new user for the app.
"""
@app.route("/register")
def register():
    return render_template("register.html")

"""
Method for account creation.
- Checks if the added username and password are valid.
- If username and password are not valid, shows error message and redirects to /register
- If username and password are valid, creates a new user, creates a table in database for their own collection and redirects to index
"""
@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        flash("ERROR: Passwords don't match")
        return redirect("/register")
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        flash("ERROR: Username already taken")
        return redirect("/register")
    
    try:
        db.execute(f"CREATE TABLE IF NOT EXISTS `{username}` (id INTEGER PRIMARY KEY, name TEXT)")
    except Exception as e:
        return f"ERROR: Error creationg a new table: {str(e)}"
    
    flash("Account created!")
    return redirect("/")

"""
Method for logging in.
- Checks if the added username and password are valid.
- If username and password are not valid, shows error message and redirects to /login
- If username and password are valid, starts a session for the user and redirects to index
"""
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    sql = "SELECT password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])
    if len(result) == 0:
        flash("ERROR: Username not found")
        return redirect("/login")
    stored_hash = result[0]["password_hash"]
    if not check_password_hash(stored_hash, password):
        flash("ERROR: wrong  password")
        return redirect("/login")
    session["username"] = username    
    update_name(username)
    return redirect("/")

"""
Method that ends the current user's session, then redirects to index
"""
@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")


@app.route("/new_card")
def new_card():
    # get target from query string, default to global
    target = request.args.get("target", "global")
    if target == "private" and "username" not in session:
        flash("Please log in to add to your personal collection.")
        return redirect(url_for("login"))
    
    return render_template("new_card.html", target=target)

@app.route("/send_card", methods=["POST"])
def send_card():
    content = request.form.get("content", "").strip()
    target = request.form.get("target", "global")

    if not content:
        flash("No card name provided.")
        return redirect("/")

    table_name = ""
    
    if target == "private":
        if "username" not in session:
            flash("You must be logged in to add to personal collection.")
            return redirect(url_for("login"))
        table_name = session["username"]
        
    elif target == "global":
        table_name = "cards"
    else:
        flash("Couldn't add a card, no valid table name received")
        return redirect("/")

    db.execute(f"CREATE TABLE IF NOT EXISTS `{table_name}` (id INTEGER PRIMARY KEY, name TEXT)")
    db.execute(f"INSERT INTO `{table_name}` (name) VALUES (?)", (content,))
        
    if target == "private":
        flash(content + " added to personal collection.")
        return redirect("/personal_card_list")
    else:
        flash(content + " added to the public collection.")
        return redirect("/full_card_list")


"""
Page that let's user add a random card to the global collection.
Calls for an another method add_random_card and tjen redirects back to the global card list.
"""
@app.route("/random_card")
def random_card():
    add_random_card()
    return redirect("/full_card_list")

"""
Method that adds a random card from a list to the global database
"""
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
"""
Page that deletes a card from the global collection.
Then it redirects user to index.
"""
@app.route("/delete_card")
def delete_card():
    db.execute(
            "DELETE FROM cards WHERE id = (SELECT MAX(id) FROM cards)"
        )
    return redirect("/personal_card_list")
