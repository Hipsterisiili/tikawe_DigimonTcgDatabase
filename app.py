"""
Main application file
"""
import math
import sqlite3
import secrets
from flask import Flask, flash, redirect, render_template, request, session, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash
import items
import users
import comments
from constants import ALLOWED_RARITIES, ALLOWED_SETS, ALL_SETS

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)  # This gives you a 16-byte random URL-safe token

# Will fix this redundancy later.
@app.errorhandler(403)
def forbidden(error):
    """
    Handler for error 403
    """
    return render_template("errors/403.html", error=error), 403

@app.errorhandler(404)
def not_found(error):
    """
    Handler for error 404
    """
    return render_template("errors/404.html", error=error), 404

def check_csrf():
    """
    Helper function for checking if correct token was sent for a POST method.
    Aborts process if csrf-token was manipulated.
    """
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

def require_login():
    """
    Helper function for checking if user is logged in
    Aborts process if a method that requires login was called without logging in.
    """
    if "user_id" not in session:
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

PER_PAGE = 100

@app.route("/full_card_list/")
@app.route("/full_card_list/<int:page>")
def full_card_list(page: int = 1):
    """
    This page displays the contents of the puclic table.
    Visible to everyone even without logging in.
    Logged in user may:
    - Add a card from public table to their own collection
    Admin may:
    - Edit cards in this table
    - Delete cards from this table
    """
    if page < 1:
        return redirect(url_for("full_card_list", page=1))

    owner_id = None
    selected_set = request.args.get("set", "all")
    if selected_set != "all" and selected_set not in ALLOWED_SETS:
        selected_set = "all"

    total, err = items.get_card_count(owner_id, card_set=selected_set)
    if err:
        flash(err)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    if page > total_pages:
        return redirect(url_for("full_card_list", page=total_pages, set=selected_set))
    if page < 1:
        return redirect(url_for("full_card_list", page=1, set=selected_set))

    offset = (page - 1) * PER_PAGE
    card_list, err = items.get_card_list(
        owner_id, limit=PER_PAGE, offset=offset, card_set=selected_set
        )
    if err:
        flash(err)
    latest_card, err = items.get_latest_card(owner_id)
    if err:
        flash(err)

    user = users.get_user_by_username(session.get("username"))
    try:
        is_admin = int(user['is_admin'] or 0)
    except Exception:
        is_admin = 0

    return render_template(
        "cards/full_card_list.html",
        count=total,
        card_list=card_list,
        latest_card=latest_card,
        is_admin=is_admin,
        page=page,
        total_pages=total_pages,
        sets=ALL_SETS,
        selected_set=selected_set,
        per_page=PER_PAGE
    )

@app.route("/personal_card_list")
def personal_card_list():
    """
    This page displays the user's own collection.
    Only visible if logged in.
    User may:
    - Add specific or random cards to their own collection
    - Edit cards to their own collection
    - Delete cards from their own collection
    """
    require_login()

    owner_id = session["user_id"]
    favorites_only = request.values.get("favorites_only", "false").lower() == "true"
    card_amount, err = items.get_card_count(owner_id)
    if err:
        flash(err)
    card_list, err = items.get_card_list(
        owner_id,
        limit=100,
        offset=0,
        card_set=None,
        favorites_only=favorites_only
    )
    if err:
        flash(err)
    comment_list = comments.get_comment_list_using_receiver_name(session["username"])

    return render_template(
        "cards/personal_card_list.html",
        count=card_amount,
        card_list=card_list,
        comment_list=comment_list,
        favorites_only=favorites_only
    )


@app.route("/user_collection/<username>")
def user_collection(username):
    """
    Function for finding an other user's collection (name given in url)
    User can view and comment (if logged in) other user's collection
    Returns 
    -If displaying logged in user's personal list: rendered personal_card_list.html
    -If displaying someone else's personal list: rendered user_collection.html
    """

    if not users.get_user_by_username(username):
        flash("User not found.")
        return redirect(url_for("user_list"))

    user_row = users.get_user_by_username(username)
    owner_id = int(user_row["id"])
    favorites_only = request.values.get("favorites_only", "false").lower() == "true"

    card_list, err = items.get_card_list(
            owner_id,
            limit=100,
            offset=0,
            card_set=None,
            favorites_only=favorites_only
        )
    if err:
        flash(err)

    card_amount, err = items.get_card_count(owner_id)
    if err:
        flash(err)

    latest_card, err = items.get_latest_card(owner_id)
    if err:
        flash(err)

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
        latest_card=latest_card,
        favorites_only=favorites_only
        )


@app.route('/add_comment', methods=['POST'])
def add_comment():
    """
    Using this page user can add a comment to another user's collection.
    The comment is stored in the database and can be viewed by anyone.
    Redirects back to the page where the comment was added from.
    """
    check_csrf()
    require_login()

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

    comments.add_comment(commenter_id, receiver_id, comment_text)

    flash('Comment posted')
    return redirect(request.referrer or url_for('user_collection', username=receiver_username))

@app.route('/delete_comment', methods=['POST'])
def delete_comment():
    """
    User can delete a comment from their collection from the database.
    Comment is identified by the id given as parameter
    Redirects back to the personal card list.
    """
    check_csrf()
    require_login()
    comment_id = request.form.get('comment_id', '').strip()

    if not comment_id:
        flash('Missing comment id')
        return redirect(request.referrer or url_for('index'))

    try:
        comment_id_int = int(comment_id)
    except ValueError:
        flash('Invalid comment id')
        return redirect(request.referrer or url_for('index'))

    # Permission to delete comment is checked within method.
    delete_succesful = comments.delete_comment(comment_id_int)
    if not delete_succesful:
        abort(403)
    return redirect(url_for('personal_card_list'))


@app.route("/register")
def register():
    """
    Page for creating a new user for the app.
    Renders the register page.
    """
    return render_template("accounts/register.html")

@app.route("/create", methods=["POST"])
def create():
    """
    Function for creating a new user for the app.
    - Checks if the added username and password are valid.
    - If username and password are not valid redirects to /register
    - If username and password are valid, creates a new user
    - When user is created their own collection in database is generated
    - Then redirects to index
    """
    username = request.form["username"].strip()
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    username, err = users.validate_new_account_input(username, password1, password2)
    if err:
        flash(err)
        return redirect(url_for("register"))

    password_hash = generate_password_hash(password1)

    try:
        users.insert_user(username, password_hash)
    except sqlite3.IntegrityError:
        flash("ERROR: Username already taken")
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
    Redirects to index if loginn  was successful.
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

    user_id = users.check_login(username, password)
    if not user_id:
        flash("ERROR: login failed")
        return redirect("/login")

    session["user_id"] = user_id
    session["username"] = username
    session["csrf_token"] = secrets.token_hex(16)
    return redirect("/")

@app.route("/logout")
def logout():
    """
    Method that ends the current user's session, 
    Then redirects to index
    """
    del session["username"]
    del session["user_id"]
    del session["csrf_token"]
    return redirect("/")

@app.route("/user_list")
def user_list():
    """
    Show all users, or users matching the optional query parameter.
    """
    query = request.args.get("query", "").strip()
    if query:
        rows = users.search_user_by_username(query)
    else:
        rows = users.get_all_users()
    return render_template("accounts/user_list.html", user_list=rows, query=query)

@app.route("/new_card")
def new_card():
    """
    A form for adding a new card with the given data to the database.
    Function requires a target parameter in the url, which can be either "private" or "global".
    - If target is "private", the card will be added to the user's personal collection.
    - If target is "global" or not provided, card will be added to the global collection.
    Redirects to the full_card_list or personal_card_list depending on where the card was added.
    """
    require_login()
    target = request.args.get("target", "global")
    if target == "private" and "username" not in session:
        flash("Please log in to add to your personal collection.")
        return redirect(url_for("login"))
    if target == "global":
        user = users.get_user_by_username(session.get("username"))
        try:
            is_admin = int(user['is_admin'] or 0)
        except (KeyError, TypeError, ValueError):
            is_admin = 0

        if not is_admin:
            abort(403)


    default_name = request.args.get("card_name", "")
    default_rarity = request.args.get("rarity", "")
    default_set = request.args.get("card_set", "BT1")
    default_suffix = request.args.get("card_number_suffix", "001")

    return render_template(
        "cards/new_card.html",
        target=target,
        sets=ALL_SETS,
        current_set=default_set,
        default_rarity=default_rarity,
        default_name=default_name,
        default_suffix=default_suffix
    )

@app.route("/send_card", methods=["POST"])
def send_card():
    """
    A method that adds a new card with the given data to the database.
    Function takes card's contents as parameters".
    - If target is "private", the card will be added to the user's personal collection.
    - If target is "global" or not provided, card will be added to the global collection.
    Redirects to the full_card_list or personal_card_list depending on where the card was added.
    """
    check_csrf()
    require_login()
    card_name = request.form.get("card_name", "").strip()
    card_set = request.form.get("card_set", "").strip() or None
    suffix = request.form.get("card_number_suffix", "").strip()
    rarity = request.form.get("rarity", "").strip() or None
    target = request.form.get("target", "global")

    card_name, rarity, card_number, err = items.check_card_elements(
        card_name, rarity, card_set, suffix
        )
    if err:
        flash(err)
        return redirect(url_for(
            "new_card",
            target=target,
            card_name=card_name,
            rarity=rarity or "",
            card_set=card_set or "",
            card_number_suffix=suffix or ""
        ))

    owner_id, err = items.table_for_target(target, session)
    if err:
        flash(err)
        return redirect(url_for("login") if "Please log in" in err else "/")

    # check duplicate only in public table
    if owner_id is None and items.find_card_id_by_card_number(card_number, None) != 0:
        flash("A card with this id already exists in the public database")
        return redirect(url_for("new_card", target=target))

    items.add_card(owner_id, card_name, card_number, rarity)

    if owner_id is not None:
        flash(card_name + " added to personal collection.")
        return redirect("/personal_card_list")
    flash(card_name + " added to the public collection.")
    return redirect("/full_card_list")


@app.route("/edit_card", methods=["GET"])
def edit_card_form():
    """
    A page for editing a card in the database.
    Function requires a target parameter in the url, which can be either "private" or "global".
    - If target is "private", the card will be edited in the user's personal collection.
    - If target is "global" or not provided, card will be edited in the global collection
    Renders the form if valid values are received.
    """
    require_login()
    target = request.args.get("target", "global")
    try:
        id_int = int(request.args.get("id"))
    except (TypeError, ValueError):
        flash("Invalid card id")
        return redirect(url_for("full_card_list"))

    owner_id, err = items.table_for_target(target, session)
    if err:
        flash(err)
        return redirect(url_for("login") if "Please log in" in err else "/")

    card = items.find_card_by_id(id_int, owner_id)
    if not card:
        flash("Card not found")
        return redirect(url_for("full_card_list" if owner_id is None else "personal_card_list"))

    # build card_set/suffix from card['card_number']
    cn = card['card_number'] or ""
    parts = str(cn).rsplit("-", 1)
    card_set, suffix = (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")

    return render_template(
        "cards/edit_card.html",
        target=target,
        id=card["id"],
        card_name=card["name"],
        rarity=card["rarity"] or "",
        card_set=card_set or "",
        card_number_suffix=suffix or "",
        sets=ALL_SETS,
        rarities=ALLOWED_RARITIES
    )

@app.route("/edit_card", methods=["POST"])
def edit_card_submit():
    """
    A method for editing a card according to the given parameters in the database.
    Redirects to the full_card_list or personal_card_list depending on where the card was edited.
    """
    check_csrf()
    require_login()
    target = request.form.get("target", "global")
    card_name = request.form.get("card_name", "").strip()
    rarity = request.form.get("rarity") or None
    card_set = request.form.get("card_set", "").strip()
    suffix = request.form.get("card_number_suffix", "").strip()

    ## Unlike when adding a card, the primary key id must be known when editing a card.
    try:
        id = int(request.form.get("id"))
    except (TypeError, ValueError):
        flash("Invalid id")
        return redirect("/full_card_list")

    # Validate fields
    card_name, rarity, card_number, err = items.check_card_elements(
        card_name, rarity or None, card_set, suffix
        )
    if err:
        flash(err)
        # redirect back to the edit form, preserving submitted values so the form can prefill
        return redirect(url_for(
            "edit_card_form",
            id=id,
            target=target,
            card_name=card_name,
            rarity=rarity or "",
            card_set=card_set or "",
            card_number_suffix=suffix or ""
        ))

    # Resolve owner_id (None means public)
    owner_id, table_err = items.table_for_target(target, session)
    if table_err:
        flash(table_err)
        if "Please log in" in table_err:
            return redirect(url_for("login"))
        # non-login table error -> return back to the edit form
        return redirect(url_for("edit_card_form", id=id, target=target))

    # permission: if editing private card, ensure owner or admin
    if owner_id is not None:
        user_row = users.get_user_by_username(session.get("username"))
        is_admin = False
        try:
            is_admin = bool(int(user_row['is_admin'] or 0))
        except Exception:
            is_admin = False
        if not is_admin and owner_id != session.get("user_id"):
            abort(403)

    items.edit_card(id, owner_id, card_name, card_number, rarity)

    if owner_id is None:
        flash(f"{card_name} updated in public collection.")
        return redirect("/full_card_list")
    flash(f"{card_name} updated in private collection.")
    return redirect("/personal_card_list")

@app.route("/delete_card", methods=["POST"])
def delete_card():
    """
    Page that deletes a card from the global collection.
    The id of the card to be deleted is given as a parameter in the form.
    The target parameter in the form determines where the card is deleted from:
    - If target is "private", the card will be deleted from the user's personal collection.
    - If target is "global" or not provided, card will be deleted from the global collection.
    Then it redirects user to index.
    """
    check_csrf()
    require_login()
    target = request.form.get("target", "global")
    name = request.form.get("name", "")
    owner_id, err = items.table_for_target(target, session)
    if err:
        flash(err)
        return redirect(url_for("login") if "Please log in" in err else "/")

    try:
        id_int = int(request.form.get("id"))
    except (TypeError, ValueError):
        flash("Invalid id")
        return redirect("/")

    # permission: allow admin to delete any, owners to delete own private items only
    if owner_id is not None:
        user_row = users.get_user_by_username(session.get("username"))
        is_admin = False
        try:
            is_admin = bool(int(user_row['is_admin'] or 0))
        except Exception:
            is_admin = False
        if not is_admin and owner_id != session.get("user_id"):
            abort(403)

    items.delete_card(id_int, owner_id)

    if owner_id is None:
        flash(f"{name} deleted from public collection.")
        return redirect("/full_card_list")
    flash(f"{name} deleted from private collection.")
    return redirect("/personal_card_list")

@app.route("/toggle_favorite", methods=["POST"])
def toggle_favorite():
    """
    Method for favoriting or unfavoriting a card..
    The target card's id is receiver fromm a from as id.
    """
    card_id = request.form.get("id", type=int)
    favorites_only = request.values.get("favorites_only", "false").lower() == "true"

    if card_id is None:
        flash("Missing card id.", "error")
        return redirect(url_for("personal_card_list"))

    items.toggle_favorite_by_id(card_id, session)
    return redirect(url_for("personal_card_list", favorites_only=favorites_only))

if __name__ == "__main__":
    app.run(debug=True)
