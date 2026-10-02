"""
Main application file
"""
import random
import sqlite3
import re
import secrets
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import db

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)  # This gives you a 16-byte random URL-safe token

@app.route("/")
def index():
    """
    Front page of the app containing: 
    - info on whether the user is logged in or not
    - link to the global collection
    - link to the private collection if logged in
    """
    return render_template("index.html")

@app.route("/full_card_list")
def full_card_list():
    """
    This page displays the global collection.
    User may:
    - Add either specific or random cards to the global collection
    - Delete cards from global collection
    """
    card_amount_result = db.query("SELECT COUNT(*) FROM public_digimon_cards")
    card_amount = card_amount_result[0][0] if card_amount_result else 0
    card_list = db.query("SELECT id, name, card_number, rarity FROM public_digimon_cards ORDER BY card_number")
    latest_card_result = db.query("SELECT name FROM public_digimon_cards ORDER BY id DESC LIMIT 1")
    latest_card = latest_card_result[0][0] if latest_card_result else None

    return render_template(
        "cards/full_card_list.html",
        count=card_amount,
        card_list=card_list,
        latest_card=latest_card
    )

@app.route("/personal_card_list")
def personal_card_list():
    """
    This page displays the user's own collection.
    User may:
    - Add specific or random cards to their own collection
    - Delete cards from their own collection
    """
    private_table_name = sanitize_table_name("personal_collection_"+ request.form["username"])

    card_amount_result = db.query(f"SELECT COUNT(*) FROM `{private_table_name}`")
    card_amount = card_amount_result[0][0] if card_amount_result else 0
    card_list = db.query(f"SELECT id, name, card_number, rarity FROM `{private_table_name}` ORDER BY card_number")

    return render_template(
        "cards/personal_card_list.html", 
        count=card_amount,
        card_list=card_list
    )

@app.route("/user_collection/<username>")
def user_collection(username):
    """
    Function for finding an other user's collection (name given in url)
    User can view and comment (TODO) other user's collection 
    Returns 
    -If displaying logged in user's personal list: rendered personal_card_list.html
    -If displaying someone else's personal list: rendered user_collection.html
    """

    list_owner = username
    table_name = sanitize_table_name("personal_collection_" + list_owner)
    if not table_name:
        flash("Invalid username.")
        return redirect(url_for("users"))

    user_exists = db.query("SELECT 1 FROM users WHERE username = ? LIMIT 1", (list_owner,))
    if not user_exists:
        flash("User not found.")
        return redirect(url_for("users"))

    try:
        card_amount_result = db.query(f'SELECT COUNT(*) FROM "{table_name}"')
        card_amount = card_amount_result[0][0] if card_amount_result else 0
        card_list = db.query(f'SELECT id, name, card_number, rarity FROM "{table_name}" ORDER BY card_number')
        latest_res = db.query(f'SELECT name FROM "{table_name}" ORDER BY id DESC LIMIT 1')
        latest_card = latest_res[0][0] if latest_res else None
    except sqlite3.OperationalError:
        card_amount = 0
        card_list = []
        latest_card = None

    if ("username" in session and session["username"] == list_owner):
        return render_template(
                "cards/personal_card_list.html",
                count=card_amount,
                card_list=card_list,
            )

    return render_template(
        "cards/user_collection.html",
        owner=list_owner,
        count=card_amount,
        card_list=card_list,
        latest_card=latest_card
    )


@app.route("/register")
def register():
    """
    Page for creating a new user for the app.
    """
    return render_template("accounts/register.html")

@app.route("/create", methods=["POST"])
def create():
    """
    Method for account creation.
    - Checks if the added username and password are valid.
    - If username and password are not valid, shows error message and redirects to /register
    - If username and password are valid, creates a new user, creates a table in database for their own collection and redirects to index
    """
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        flash("ERROR: Passwords don't match")
        return redirect(url_for("register"))
    if len(username) < 3:
        flash("Your username must be at least 3 characters long")
        return redirect(url_for("register"))

    if len(password1) < 3:
        flash("Your password must be at least 3 characters long")
        return redirect(url_for("register"))
    
    password_hash = generate_password_hash(password1)

    table_name = sanitize_table_name("personal_collection_"+ username)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        flash("ERROR: Username already taken")
        return redirect("/register")

    try:
        db.execute(
            f"CREATE TABLE IF NOT EXISTS \"{table_name}\" ("
            "id INTEGER PRIMARY KEY, "
            "name TEXT NOT NULL, "
            "card_number TEXT, "
            "rarity TEXT CHECK (rarity IS NULL OR rarity IN ('C','U','R','UR','SEC','P','SR'))"
            ")"
        )

    except Exception as e:
        return f"ERROR: Error creating a new table: {str(e)}"

    flash("Account created!")
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Method for logging in.
    - Checks if the added username and password are valid.
    - If username and password are not valid, shows error message and redirects to /login
    - If username and password are valid, starts a session for the user and redirects to index
    """
    if request.method == "GET":
        return render_template("accounts/login.html")

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
    return redirect("/")

@app.route("/logout")
def logout():
    """
    Method that ends the current user's session, then redirects to index
    """
    del session["username"]
    return redirect("/")

def find_card_using_card_id(card_id, target):
    """
    Look up the primary key id for a given card_number (card_id).
    Returns:
      - the integer primary key id if found
      - 0 if not found or on invalid input / error
    """

    if not isinstance(card_id, str):
        return 0
    card_id = card_id.strip()
    if not card_id:
        return 0
    table_name = ""
    if target == "private":
        table_name = sanitize_table_name("personal_collection_"+ request.form["username"])
    else:
        table_name = "public_digimon_cards" 
    try:
        rows = db.query(
            f"SELECT id FROM {table_name} WHERE card_number = ? LIMIT 1",
            (card_id,)
        )
    except Exception:
        return 0

    if not rows:
        return 0

    # rows[0] is an sqlite3.Row, so you can access by column name
    return rows[0]["id"]

@app.route("/users")
def users():
    """
    A page for displaying a list of all current users for the app
    """
    rows = db.query("SELECT username, created_at, is_admin FROM users ORDER BY username")
    return render_template("accounts/users.html", users=rows)

import sqlite3
from flask import abort, flash, session, url_for, redirect

@app.route("/new_card")
def new_card():
    # get target from query string, default to global
    target = request.args.get("target", "global")
    if target == "private" and "username" not in session:
        flash("Please log in to add to your personal collection.")
        return redirect(url_for("login"))

    return render_template("cards/new_card.html", target=target)

@app.route("/send_card", methods=["POST"])
def send_card():
    card_name = request.form.get("card_name", "").strip()
    target = request.form.get("target", "global")
    rarity = request.form.get("rarity", "").strip() or None
    card_set = request.form.get("card_set", "").strip() or None
    suffix = request.form.get("card_number_suffix", "").strip()

    if card_name and is_card_name_valid(card_name):
        card_name = sanitize_card_name(card_name)
    else:
        flash("No valid card name provided.")
        return redirect(url_for("new_card", target=target))
    if rarity and rarity not in {"C","U","R","UR","SEC","P","SR"}:
        flash("Invalid rarity selected.")
        return redirect(url_for("new_card", target=target))
    if suffix:
        card_number = card_set + "-" + suffix
    else:
        card_number = card_set + "-" + "000"
    if target == "global" and find_card_using_card_id(card_number, target) != 0:
        flash("A card with this id already exists in the public database")
        return redirect(url_for("new_card", target=target))

    table_name = ""

    if target == "private":
        if "username" not in session:
            flash("You must be logged in to add to personal collection.")
            return redirect(url_for("login"))
        table_name = sanitize_table_name("personal_collection_"+ request.form["username"])

    elif target == "global":
        table_name = "public_digimon_cards"
    else:
        flash("Couldn't add a card, no valid table name received")
        return redirect("/")

    db.execute(
        f"CREATE TABLE IF NOT EXISTS `{table_name}` ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT NOT NULL, "
        "card_number TEXT, "
        "rarity TEXT CHECK (rarity IS NULL OR rarity IN ('C','U','R','UR','SEC','P','SR'))"
        ")"
    )
    db.execute(
        f"INSERT INTO `{table_name}` (name, card_number, rarity) VALUES (?, ?, ?)",
        (card_name, card_number, rarity)
    )

    if target == "private":
        flash(card_name + " added to personal collection.")
        return redirect("/personal_card_list")
    flash(card_name + " added to the public collection.")
    return redirect("/full_card_list")


@app.route("/random_card")
def random_card():
    """
    Page that let's user add a random card to the global collection.
    Calls for an another method add_random_card and tjen redirects back to the global card list.
    """
    add_random_card()
    return redirect("/full_card_list")

def is_card_name_valid(name: str) -> bool:
    """
    Validate the raw input before any sanitization.
    Rules:
      - must be a str
      - after trimming leading/trailing whitespace it must be non-empty
      - the trimmed string must be at most 20 characters long

    Returns True when valid, False otherwise.
    """
    if not isinstance(name, str):
        return False
    trimmed = name.strip()
    if not trimmed:
        return False
    if len(trimmed) > 20:
        return False
    return True

import re

def sanitize_table_name(name):
    """
    Return a safe table name (same scheme used when creating per-user tables),
    or None if invalid. Allows letters, digits and underscores, and no leading digit.
    """
    if not isinstance(name, str):
        return None
    s = re.sub(r'\W', '_', name)   # convert non-word chars to underscores
    return s if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', s) else None


def sanitize_card_name(name: str) -> str:
    """
    Sanitize the input string (assumes caller already validated or chooses to call it).
    Operations performed:
      - non-strings -> returns empty string
      - collapse consecutive whitespace into a single space
      - strip leading/trailing whitespace
      - ensure first character is uppercase (leaves the rest unchanged)

    Returns the sanitized string (may be empty if input was not a string or all whitespace).
    """
    if not isinstance(name, str):
        return ""
    s = re.sub(r'\s+', ' ', name).strip()
    if not s:
        return ""
    s = s[0].upper() + s[1:]
    return s

def add_random_card():
    """
    Method that adds a random card from a list to the global database
    """
    cards = [
        ("Agumon", "P-001", "P"),
        ("Biyomon", "P-002", "P"),
        ("Gabumon", "P-003", "P"),
        ("Gomamon", "P-004", "P"),
        ("Patamon", "P-005", "P"),
        ("Gatomon", "P-006", "P")
    ]

    name, card_number, rarity = random.choice(cards)

    try:
        db.execute(
            "INSERT INTO public_digimon_cards (name, card_number, rarity) VALUES (?, ?, ?)",
            (name, card_number, rarity)
        )
    except sqlite3.IntegrityError:
        flash("Tried to add an already existing card.")


@app.route("/edit_card", methods=["GET"])
def edit_card_form():
    """
    Page that edits a requested data element based on user's actions
    """
    card_id = request.args.get("id")
    target = request.args.get("target", "global")

    if not card_id:
        flash("No card id provided")
        return redirect(url_for("full_card_list"))

    try:
        card_id_int = int(card_id)
    except ValueError:
        flash("Invalid card id")
        return redirect(url_for("full_card_list"))

    if target == "private":
        if "username" not in session:
            flash("Please log in")
            return redirect(url_for("login"))
        table = sanitize_table_name("personal_collection_"+ request.form["username"])
    else:
        table = "public_digimon_cards"

    row = db.query(f'SELECT id, name, card_number, rarity FROM "{table}" WHERE id = ?', (card_id_int,))
    if not row:
        flash("Card not found")
        return redirect(url_for("full_card_list" if target=="global" else "personal_card_list"))

    card = row[0]

    card_set = ""
    suffix = ""
    if card["card_number"]:
        parts = str(card["card_number"]).rsplit("-", 1)
        if len(parts) == 2:
            card_set, suffix = parts[0], parts[1]
        else:
            card_set = parts[0]

    return render_template(
        "cards/edit_card.html",
        target=target,
        id=card["id"],
        card_name=card["name"],
        rarity=card["rarity"] or "",
        card_set=card_set or "",
        card_number_suffix=suffix or ""
    )

@app.route("/edit_card", methods=["POST"])
def edit_card_submit():
    id = request.form.get("id")
    target = request.form.get("target", "global")
    name = request.form.get("card_name", "").strip()
    rarity = request.form.get("rarity") or None
    card_set = request.form.get("card_set", "").strip()
    suffix = request.form.get("card_number_suffix", "").strip()

    try:
        id_int = int(id)
    except (TypeError, ValueError):
        flash("Invalid id")
        return redirect("/full_card_list")

    card_number = card_set + "-" + suffix
    if target == "private":
        if "username" not in session:
            flash("Please log in")
            return redirect("{{ url_for('login') }}")
        table = sanitize_table_name("personal_collection_"+ request.form["username"])
    elif target == "global":
        table = "public_digimon_cards"
    else:
        flash(f"Incorrect table name, {target} given")
        return redirect("/")

    db.execute(
        f'UPDATE "{table}" SET name = ?, card_number = ?, rarity = ? WHERE id = ?',
        (name, card_number, rarity, id_int)
    )

    if table == "public_digimon_cards":
        flash(f"{name} updated in public collection.")
        return redirect("/full_card_list")
    flash(f"{name} updated in private collection.")
    return redirect("/personal_card_list")

@app.route("/delete_card", methods=["POST"])
def delete_card():
    """
    Page that deletes a card from the global collection.
    Then it redirects user to index.
    """
    target = request.form.get("target", "global")
    table_name = ""
    name = request.form.get("name", "")
    id_str = request.form.get("id")

    if target == "global":
        table_name = "public_digimon_cards"
    elif target == "private":
        table_name = sanitize_table_name("personal_collection_"+ request.form["username"])
    else:
        flash(f"Incorrect table name, {target} given")
        return redirect("/")

    if not id_str:
        flash("No id received, cannot delete anything")
        return redirect("/")

    try:
        id_int = int(id_str)
    except ValueError:
        flash("Invalid id")
        return redirect("/")

    db.execute(f'DELETE FROM "{table_name}" WHERE id = ?', [id_int])
    if table_name == "public_digimon_cards":
        flash(f"{name} deleted from public collection.")
        return redirect("/full_card_list")
    flash(f"{name} deleted from private collection.")
    return redirect("/personal_card_list")
