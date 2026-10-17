"""
Helper functions related to cards in the database.
Validations for table names and item values
Methods for finding items from database
Methods for adding items to database
Methods for deleting items from database
Methods for editing items in database
"""
import re
import sqlite3
from flask import flash
from constants import ALLOWED_RARITIES, ALLOWED_SETS, CARD_ORDER_SQL
import db
import users

def is_card_name_valid(name: str) -> bool:
    """ Validate the raw input before any sanitization.
    Rules: 
    - must be a str.
    - collapse consecutive whitespace into a single space.
    - remove leading/trailing whitespace -
    The resulting string must be non-empty and at most 20 characters long """
    if not isinstance(name, str):
        return False
    collapsed = re.sub(r'\s+', ' ', name).strip()
    if not collapsed:
        flash("Card name cannot be empty or whitespace only.")
        return False
    # Shortest existing card names are Pal, Mon (Both 3 letters)
    # Longest existing card name is:
    # Metropolitan Police Department, Community Safety Bureau,
    # Cyber Crime Division, Investigation Unit 11,
    # Digimon Crime Response Team (121 characters)
    if len(collapsed) < 3 or len(collapsed) >130:
        flash("Card name must be between 3 and 130 characters long")
        return False
    return True

def _sanitize_card_name(name: str) -> str:
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

def table_for_target(target: str, session) -> tuple[int | None, str | None]:
    """
    Return (owner_id, error_message).
    Owner_id is None for public table, or an int user id for private.
    error_message is None when OK.
    """
    if target == "private":
        username = session.get("username")
        if not username:
            return None, "Please log in"
        user = users.get_user_by_username(username)
        if not user:
            return None, "Please log in"
        try:
            return int(user["id"]), None
        except Exception:
            return None, "Internal error: could not determine user id"
    if target == "global":
        return None, None
    return None, f"Incorrect table name, {target} given"


def check_card_elements(
    card_name: str, rarity: str, card_set: str, suffix: str ) -> tuple[str, str, str, str]:
    """
    Check validity of card's name, rarity, and error message.
    Return (rarity, card_id, error_message). error_message None if OK.
    """
    errors = []
    if card_name and is_card_name_valid(card_name):
        card_name = _sanitize_card_name(card_name)
    else:
        errors.append("No valid card name provided.")
    if rarity and rarity not in ALLOWED_RARITIES:
        errors.append("Invalid rarity selected.")
    if card_set and card_set not in ALLOWED_SETS:
        errors.append("Invalid set name selected.")
    if suffix:
        card_number = card_set + "-" + suffix
    else:
        card_number = card_set + "-" + "000"
    err = "\n".join(errors)
    return card_name, rarity, card_number, err

def get_card_count(owner_id, card_set=None):
    """
    Count and return amount of cards in table as int along with an error message.
    In case of errors, returns 0 in place of amount.
    Error_string is '' when OK, otherwise contains a message.
    If a set is given as a parameter, count only cards with a matching set
    If owner_id is None -> count public_digimon_cards.
    If owner_id is int -> count private_digimon_cards WHERE owner_id = ?
    """
    try:
        if owner_id is None:
            table = "public_digimon_cards"

            if card_set and card_set != "all":
                sql = (
                    f'SELECT COUNT(*) AS cnt FROM "{table}" '
                    "WHERE card_number LIKE ?"
                )
                params = [f"{card_set}-%"]
            else:
                sql = f'SELECT COUNT(*) AS cnt FROM "{table}"'
                params = []
        else:
            table = "private_digimon_cards"

            if card_set and card_set != "all":
                sql = (
                    f'SELECT COUNT(*) AS cnt FROM "{table}" '
                    "WHERE owner_id = ? AND card_number LIKE ?"
                )
                params = [owner_id, f"{card_set}-%"]
            else:
                sql = (
                    f'SELECT COUNT(*) AS cnt FROM "{table}" '
                    "WHERE owner_id = ?"
                )
                params = [owner_id]

        rows = db.query(sql, params)
        return (int(rows[0]["cnt"]) if rows else 0, "")

    except sqlite3.Error:
        return (0, "Database error: failed to count cards.")

def get_card_list(
    owner_id,
    limit=100,
    offset=0,
    card_set=None,
    favorites_only=False,
    conditions=False,
):
    """
    Return a list of cards as dicts from the requested table and error string.
    If favorites_only is True and owner_id is not None, return only cards
    that have an item_classes row with title='Favorite' and value='yes'.
    If conditions is True and owner_id is not None, include a 'condition'
    column in each returned row (NULL if no condition set).
    """
    try:
        if owner_id is None:
            # Public table: Show entire contents, but chopped into 100 card pieces
            table = "public_digimon_cards"

            if card_set and card_set != "all":
                sql = (
                    f'SELECT id, name, card_number, rarity FROM "{table}" p '
                    "WHERE card_number LIKE ? "
                    f"ORDER BY {CARD_ORDER_SQL} "
                    "LIMIT ? OFFSET ?"
                )
                params = [f"{card_set}-%", limit, offset]
            else:
                sql = (
                    f'SELECT id, name, card_number, rarity FROM "{table}" p '
                    f"ORDER BY {CARD_ORDER_SQL} "
                    "LIMIT ? OFFSET ?"
                )
                params = [limit, offset]

        else:
            # Private table: optionally filter by favorites and include condition
            table = "private_digimon_cards"

            # Choose a clause depending on whether condition is asked for or not
            if conditions:
                select_clause = (
                    "SELECT p.id, p.name, p.card_number, p.rarity, "
                    "(SELECT ic.value FROM item_classes ic "
                    "WHERE ic.item_id = p.id AND ic.title = 'Condition' "
                    "ORDER BY ic.id LIMIT 1) AS condition "
)
            else:
                select_clause = (
                    "SELECT p.id, p.name, p.card_number, p.rarity "
                )

            base_sql = (
                select_clause
                + f'FROM "{table}" p WHERE p.owner_id = ? '
            )
            params = [owner_id]

            # Filter by card_set if card_set given as parameter
            if card_set and card_set != "all":
                base_sql += "AND p.card_number LIKE ? "
                params.append(f"{card_set}-%")

            # Filter favorites if favorites_only
            if favorites_only:
                base_sql += (
                    "AND EXISTS ("
                    " SELECT 1 FROM item_classes ic2 "
                    " WHERE ic2.item_id = p.id AND ic2.title = 'Favorite' "
                    " AND ic2.value = 'yes') "
                )

            # Finalize ordering and paging
            sql = (
                base_sql
                + f"ORDER BY {CARD_ORDER_SQL} "
                "LIMIT ? OFFSET ?"
            )
            params.extend([limit, offset])

        rows = db.query(sql, params)
        return ([dict(r) for r in rows] if rows else [], "")

    except sqlite3.Error:
        return ([], "Database error: failed to fetch cards.")


def get_card_number_from_table(owner_id: int | None) -> int:
    """
    Return the number of cards for the given owner.
    - owner_id is None -> count public_digimon_cards
    - owner_id is an int -> count private_digimon_cards WHERE owner_id = ?
    Returns 0 if the table does not exist or on error.
    """
    try:
        if owner_id is None:
            sql = 'SELECT COUNT(*) AS count FROM "public_digimon_cards"'
            params = []
        else:
            sql = (
                'SELECT COUNT(*) AS count FROM "private_digimon_cards" '
                "WHERE owner_id = ?"
            )
            params = [owner_id]

        rows = db.query(sql, params)
        return int(rows[0]["count"]) if rows else 0

    except sqlite3.Error:
        return 0

def get_latest_card(owner_id):
    """
    Return the name of the latest added card if any and an error string if there are errors.
    If no latest card is found, NONE is returned in its place.
    error_string is '' when OK, otherwise contains a message.
    """
    try:
        if owner_id is None:
            sql = (
                'SELECT name FROM "public_digimon_cards" '
                "ORDER BY id DESC LIMIT 1"
            )
            params = []
        else:
            sql = (
                'SELECT name FROM "private_digimon_cards" '
                "WHERE owner_id = ? ORDER BY id DESC LIMIT 1"
            )
            params = [owner_id]

        rows = db.query(sql, params)
        return (rows[0]["name"] if rows else None, "")

    except sqlite3.Error:
        return (None, "Database error: failed to fetch latest card.")

def add_card(
    owner_id: int | None,
    name: str,
    card_number: str,
    rarity: str,
) -> int | None:
    """
    Insert a card into the public (if owner is none) or private collection.
    Return the new card ID on success, or None on failure.
    """
    if owner_id is None:
        db.execute(
            'CREATE TABLE IF NOT EXISTS public_digimon_cards ('
            'id INTEGER PRIMARY KEY, '
            'name TEXT NOT NULL, '
            'card_number TEXT, '
            "rarity TEXT CHECK (rarity IS NULL OR rarity IN "
            "('C','U','R','UR','SEC','P','SR'))"
            ')'
        )

        db.execute(
            'INSERT INTO public_digimon_cards '
            '(name, card_number, rarity) VALUES (?, ?, ?)',
            (name, card_number, rarity),
        )

    else:
        db.execute(
            'CREATE TABLE IF NOT EXISTS private_digimon_cards ('
            'id INTEGER PRIMARY KEY, '
            'name TEXT NOT NULL, '
            'card_number TEXT, '
            "rarity TEXT CHECK (rarity IS NULL OR rarity IN "
            "('C','U','R','UR','SEC','P','SR')), "
            'owner_id INTEGER NOT NULL, '
            'FOREIGN KEY(owner_id) REFERENCES users(id)'
            ')'
        )

        # Enforce per-user card limit
        card_amount, err = get_card_count(owner_id)

        if err:
            flash(err)
            return None

        if card_amount >= 100:
            flash(
                "User cannot have more than 100 cards in private collection!",
                "error",
            )
            return None

        db.execute(
            'INSERT INTO private_digimon_cards '
            '(name, card_number, rarity, owner_id) '
            'VALUES (?, ?, ?, ?)',
            (name, card_number, rarity, owner_id),
        )

    # Return the ID of the row just inserted.
    return db.last_insert_id()


def edit_card(id_int: int, owner_id: int | None, name: str, card_number: str, rarity: str) -> None:
    """
    Edit a card in the specified table.
    Card is located using the primary key id given as parameter.
    Takes the new name, card_number, and rarity as parameters.
    If owner_id is None, edits public table row with id
    If owner_id exists, edits private table row with id AND owner_id
    (so user can't edit another user's card)
    """
    if owner_id is None:
        sql = ( "UPDATE public_digimon_cards "
               "SET name = ?, card_number = ?, rarity = ? "
               "WHERE id = ?" )
        params = [name, card_number, rarity, id_int]
    else:
        sql = ( "UPDATE private_digimon_cards "
               "SET name = ?, card_number = ?, rarity = ? "
               "WHERE id = ? AND owner_id = ?" )
        params = [name, card_number, rarity, id_int, owner_id]
    db.execute(sql, params)


def delete_card(id_int: int, owner_id: int | None) -> None:
    """
    Delete a card from the specified table by its primary key id.
    If owner_id is None, deletes from public table row with id matching parameter id_int.
    If owner_id exists, deletes from private table row with id AND owner_id.
    """
    if owner_id is None:
        db.execute(
            'DELETE FROM public_digimon_cards WHERE id = ?',
            [id_int]
        )
    else:
        db.execute(
            'DELETE FROM private_digimon_cards WHERE id = ? AND owner_id = ?',
            [id_int, owner_id]
        )


def find_card_by_id(id_int: int, owner_id: int | None):
    """
    Look up a card by its primary key id.
    If owner_id is None, edits public table row with id matching parameter id_int.
    If owner_id exists, deletes from private table row with id matching parameter id_int.
    Returns:
       - the card data if found
       - None if not found or on invalid input / error
    """
    if not isinstance(id_int, int):
        return None
    try:
        if owner_id is None:
            sql = ( "SELECT id, name, card_number, rarity "
                   "FROM public_digimon_cards "
                   "WHERE id = ?" )
            params = [id_int]
        else:
            sql = ( "SELECT id, name, card_number, rarity "
                   "FROM private_digimon_cards "
                   "WHERE id = ? AND owner_id = ?" )
            params = [id_int, owner_id]
        rows = db.query(sql, params)
    except sqlite3.Error:
        return None
    return rows[0] if rows else None


def find_card_id_by_card_number(card_number: str, owner_id: int | None) -> int:
    """
    Look up the primary key id for a given card_number (card_id).
    If owner_id is None, searches public table row with card_number matching given parameter.
    If owner_id exists, searches private table row with card_number matching given parameter.
    Returns:
      - the integer primary key id if found
      - 0 if not found or on invalid input / error
    """
    if not isinstance(card_number, str):
        return 0
    card_number = card_number.strip()
    if not card_number:
        return 0
    try:
        if owner_id is None:
            sql = ( "SELECT id FROM public_digimon_cards "
                   "WHERE card_number = ? LIMIT 1" )
            params = [card_number]
        else:
            sql = ( "SELECT id FROM private_digimon_cards "
                   "WHERE owner_id = ? AND card_number = ? LIMIT 1" )
            params = [owner_id, card_number]
        rows = db.query(sql, params)
    except sqlite3.Error:
        return 0
    if not rows:
        return 0
    return rows[0]['id']

def toggle_favorite_by_id(card_id: int, session):
    """
    Changes the element in item_classes so that a card may be declared or undeclared favorite.
    Takes id referencing a card in private collection as parameter.
    Inserts a Favorite=yes row if none exists;
    Normalizes duplicate rows so that only one is kept
    Flashes error message in case of error.
    Returns True if process was successful, returns False if not.
    """
    try:
        rows = db.query("SELECT id, owner_id FROM private_digimon_cards WHERE id = ?", [card_id])
        if not rows:
            flash("Card not found.", "error")
            return False

        if not rows[0]['owner_id'] == session.get("user_id"):
            flash("This is not your card", "error")
            return False

        cfg_rows = db.query(
            "SELECT value FROM classes WHERE title = 'Favorite' AND value IN ('yes','no')"
            )
        configured = {r['value'] for r in cfg_rows} if cfg_rows else set()
        if not ({'yes', 'no'} <= configured):
            flash("Favorite values are not configured in classes table.", "error")
            return False

        sql = ( "SELECT id, value "
               "FROM item_classes "
               "WHERE item_id = ? AND title = 'Favorite' "
               "ORDER BY id" )
        fav_rows = db.query(sql, [card_id])

        if not fav_rows:
            db.execute(
                "INSERT INTO item_classes (item_id, title, value) VALUES (?, 'Favorite', 'yes')",
                [card_id]
            )
        else:
            # Keeps the first row, deletes any duplicates, then toggles first row's value
            keep_id = fav_rows[0]['id']
            keep_value = fav_rows[0]['value']

            if len(fav_rows) > 1:
                ids_to_delete = [str(r['id']) for r in fav_rows[1:]]
                placeholders = ",".join("?" for _ in ids_to_delete)
                params = [int(i) for i in ids_to_delete]
                db.execute(f"DELETE FROM item_classes WHERE id IN ({placeholders})", params)

            new_value = 'no' if keep_value == 'yes' else 'yes'
            db.execute("UPDATE item_classes SET value = ? WHERE id = ?", [new_value, keep_id])

        return True

    except sqlite3.Error as e:
        flash(f"Database error while toggling favorite: {e}", "error")
        return False

def _card_belongs_to_user(card_id: int, session) -> bool:
    """
    Check if the card exists and belongs to the logged in user.
    """

    rows = db.query(
        "SELECT owner_id FROM private_digimon_cards WHERE id = ?",
        [card_id],
    )

    if not rows:
        flash("Card not found.", "error")
        return False

    try:
        if int(rows[0]["owner_id"]) != int(session.get("user_id")):
            flash("This is not your card", "error")
            return False
    except (TypeError, ValueError):
        flash("Internal error: invalid user id", "error")
        return False
    return True

def _update_card_condition(card_id: int, new_value: str | None) -> bool:
    """
    Sets the requested condition to the requested card.
    If no condition is given (None or "None"), deletes the condition.
    """
    if new_value == "None":
        new_value = None

    cfg_rows = db.query(
        "SELECT value FROM classes WHERE title = 'Condition' ORDER BY id"
    )
    values = [row["value"] for row in cfg_rows] if cfg_rows else []

    if new_value is not None and new_value not in values:
        flash("Invalid condition value.", "error")
        return False

    rows = db.query(
        "SELECT id FROM item_classes "
        "WHERE item_id = ? AND title = 'Condition' ORDER BY id",
        [card_id],
    )

    if new_value is None:
        if rows:
            db.execute(
                "DELETE FROM item_classes "
                "WHERE item_id = ? AND title = 'Condition'",
                [card_id],
            )
        return True


    if not values:
        flash("Condition values are not configured in classes table.", "error")
        return False

    if not rows:
        db.execute(
            "INSERT INTO item_classes (item_id, title, value) "
            "VALUES (?, 'Condition', ?)",
            [card_id, new_value],
        )
        return True

    keep_id = rows[0]["id"]

    if len(rows) > 1:
        ids = [row["id"] for row in rows[1:]]
        placeholders = ",".join("?" for _ in ids)
        db.execute(
            f"DELETE FROM item_classes WHERE id IN ({placeholders})",
            ids,
        )

    db.execute(
        "UPDATE item_classes SET value = ? WHERE id = ?",
        [new_value, keep_id],
    )
    return True

def get_possible_conditions():
    """
    Finds and returns all possible card conditions from table classes.
    """
    rows = db.query(
        """
        SELECT value
        FROM classes
        WHERE title = ?
        ORDER BY id
        """,
        ["Condition"],
    )

    return [row["value"] for row in rows] if rows else []

def set_condition_by_id(
    card_id: int,
    session,
    new_value: str | None = None,
) -> bool:
    """
    Set the condition for a private card to match the one given as parameter.
    If no condition is given, deletes condition of the card, if it exists
    Return True on success, False on failure.
    """

    try:
        if not _card_belongs_to_user(card_id, session):
            return False

        return _update_card_condition(card_id, new_value)

    except sqlite3.Error as error:
        flash(f"Database error while changing condition: {error}", "error")
        return False
