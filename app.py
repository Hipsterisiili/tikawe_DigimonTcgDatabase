"""
Main application file
"""
import sqlite3
import secrets
from flask import Flask, flash, redirect, render_template, request, session, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash
import items
import users
import comments
import db

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)  # This gives you a 16-byte random URL-safe token

def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

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
    private_table_name = "personal_collection_"+ session["username"]

    card_amount = items.get_card_number_from_table(private_table_name)
    card_list = items.get_card_list_from_table(private_table_name)
    comment_list = comments.get_comment_list_using_receiver_name(session["username"])

    return render_template(
        "cards/personal_card_list.html", 
        count=card_amount,
        card_list=card_list,
        comment_list=comment_list
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

    table_name = items.sanitize_table_name("personal_collection_" + username)
    if not table_name:
        flash("Invalid username.")
        return redirect(url_for("user_list"))

    if not users.get_user_by_username(username):
        flash("User not found.")
        return redirect(url_for("user_list"))

    try:
        card_list = items.get_card_list_from_table(table_name)
        card_amount = len(card_list)
        latest_card = items.get_latest_card_from_table(table_name)
    except sqlite3.OperationalError:
        card_amount = 0
        card_list = []
        latest_card = None

    if ("username" in session and session["username"] == username):
            return render_template(
                    "cards/personal_card_list.html",
                    count=card_amount,
                    card_list=card_list,
                )
    return render_template(
        "cards/user_collection.html",
        owner=username,
        count=card_amount,
        card_list=card_list,
        latest_card=latest_card
    )

@app.route('/add_comment', methods=['POST'])
def add_comment():
    """
    Using this page user can add a comment to another user's collection.
    The comment is stored in the database and can be viewed by anyone.
    """
    check_csrf()
    
    if 'username' not in session:
        flash('Please log in to comment')
        return redirect(url_for('login'))

    commenter_username = session['username']
    receiver_username = request.form.get('receiver_username', '').strip()
    comment_text = request.form.get('comment_text', '').strip()

    if not receiver_username or not comment_text:
        flash('Missing target or empty comment')
        return redirect(request.referrer or url_for('index'))

    commenter = users.get_user_by_username(commenter_username)
    receiver = users.get_user_by_username(receiver_username)

    if not commenter or not receiver:
        flash('commenter or receiver not found')
        return redirect(request.referrer or url_for('index'))

    commenter_id = commenter['id']
    receiver_id = receiver['id']

    comments.add_comment(db, commenter_id, receiver_id, comment_text)

    flash('Comment posted')
    return redirect(request.referrer or url_for('user_collection', username=receiver_username))

@app.route('/delete_comment', methods=['POST'])
def delete_comment():
    """
    User can delete a comment regarding their collection from the database.
    """
    check_csrf()
    comment_id = request.form.get('comment_id', '').strip()

    if not comment_id:
        flash('Missing comment id')
        return redirect(request.referrer or url_for('index'))

    try:
        comment_id_int = int(comment_id)
    except ValueError:
        flash('Invalid comment id')
        return redirect(request.referrer or url_for('index'))

    comments.delete_comment(comment_id_int)

    return redirect(url_for('personal_card_list'))


@app.route("/register")
def register():
    """
    Page for creating a new user for the app.
    """
    return render_template("accounts/register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"].strip()
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    # basic validation (keep this in the route as it's request/UI logic)
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

    try:
        users.insert_user(username, password_hash)
    except sqlite3.IntegrityError:
        flash("ERROR: Username already taken")
        return redirect(url_for("register"))

    try:
        users.create_personal_table_for(username)
    except ValueError:
        flash("ERROR: Invalid username (cannot create personal table)")
        return redirect(url_for("register"))
    except Exception as e:
        flash(f"ERROR creating personal table: {e}")
        return redirect(url_for("register"))

    flash("Account created!")
    return redirect(url_for("index"))


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

    stored_hash = users.get_password_hash(username)
    if stored_hash is None:
        flash("ERROR: Username not found")
        return redirect("/login")

    if not check_password_hash(stored_hash, password):
        flash("ERROR: wrong  password")
        return redirect("/login")

    session["username"] = username
    session["csrf_token"] = secrets.token_hex(16)
    return redirect("/")

@app.route("/logout")
def logout():
    """
    Method that ends the current user's session, then redirects to index
    """
    del session["username"]
    return redirect("/")

@app.route("/user_list")
def user_list():
    """
    A page for displaying a list of all current users for the app
    """
    rows = users.get_all_users()
    return render_template("accounts/user_list.html", user_list=rows)

@app.route("/new_card")
def new_card():
    target = request.args.get("target", "global")
    if target == "private" and "username" not in session:
        flash("Please log in to add to your personal collection.")
        return redirect(url_for("login"))

    return render_template("cards/new_card.html", target=target)

@app.route("/send_card", methods=["POST"])
def send_card():
    print("SENDING")
    card_name = request.form.get("card_name", "").strip()
    card_set = request.form.get("card_set", "").strip() or None
    suffix = request.form.get("card_number_suffix", "").strip()
    rarity = request.form.get("rarity", "").strip() or None
    target = request.form.get("target", "global")

    if card_name and items.is_card_name_valid(card_name):
        card_name = items.sanitize_card_name(card_name)
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
    if target == "global" and items.find_card_using_card_id(card_number, target) != 0:
        flash("A card with this id already exists in the public database")
        return redirect(url_for("new_card", target=target))

    table_name = ""

    if target == "private":
        if "username" not in session:
            flash("You must be logged in to add to personal collection.")
            return redirect(url_for("login"))
        table_name = items.sanitize_table_name("personal_collection_"+ session["username"])

    elif target == "global":
        table_name = "public_digimon_cards"
    else:
        flash("Couldn't add a card, no valid table name received")
        return redirect("/")

    items.add_card_to_table(table_name, card_name, card_number, rarity)

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
    items.add_random_card()
    return redirect("/full_card_list")


@app.route("/edit_card", methods=["GET"])
def edit_card_form():
    """
    Page that edits a requested data element based on user's actions
    """
    id = request.args.get("id")
    target = request.args.get("target", "global")

    if not id:
        flash("No card id provided")
        return redirect(url_for("full_card_list"))

    try:
        id_int = int(id)
    except ValueError:
        flash("Invalid card id")
        return redirect(url_for("full_card_list"))

    if target == "private":
        if "username" not in session:
            flash("Please log in")
            return redirect(url_for("login"))
        table_name = items.sanitize_table_name("personal_collection_"+ session["username"])
    else:
        table_name = "public_digimon_cards"

    card = items.find_card_using_id(id_int, table_name)

    if not card:
        flash("Card not found")
        return redirect(url_for("full_card_list" if target=="global" else "personal_card_list"))

    card_set = ""
    suffix = ""
    if card[2]:
        parts = str(card[2]).rsplit("-", 1)
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
        table = items.sanitize_table_name("personal_collection_"+ session["username"])
    elif target == "global":
        table = "public_digimon_cards"
    else:
        flash(f"Incorrect table name, {target} given")
        return redirect("/")

    items.edit_card_in_table(table, id_int, name, card_number, rarity)

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
        table_name = items.sanitize_table_name("personal_collection_"+ session["username"])
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

    items.delete_card_from_table(table_name, id_int)
    if table_name == "public_digimon_cards":
        flash(f"{name} deleted from public collection.")
        return redirect("/full_card_list")
    flash(f"{name} deleted from private collection.")
    return redirect("/personal_card_list")

if __name__ == "__main__":
    app.run(debug=True)
