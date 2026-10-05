from curses import flash
import re
import random
import sqlite3
from flask import request
import db

def is_card_name_valid(name: str) -> bool: 
    """ Validate the raw input before any sanitization.
    Rules: 
    - must be a str.
    - collapse consecutive whitespace into a single space.
    - remove leading/trailing whitespace -
    The resulting string must be non-empty and at most 20 characters long """
    print("Name = ", name)
    if not isinstance(name, str):
        print("not a string")
        return False
    collapsed = re.sub(r'\s+', ' ', name).strip()
    print("Collapsed: ", collapsed)
    if not collapsed:
        flash("Card name cannot be empty or whitespace only.")
        return False
    """
    Shortest existing card names are Pal, Mon (Both 3 letters)
    Longest existing card name is Metropolitan Police Department, Community Safety Bureau, Cyber Crime Division, Investigation Unit 11, Digimon Crime Response Team (121 characters)
    """
    if len(collapsed) < 3 or len(collapsed) >130:
        flash("Card name must be between 3 and 130 characters long")
    return True

def sanitize_table_name(name: str) -> str:
    """
    Return a safe table name (same scheme used when creating per-user tables),
    or None if invalid. 
    Rules:
     - Must be a str
     - Contains only letters, digits and underscores
     - Contains no leading digit.
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

def table_for_target(target: str, session) -> tuple:
    """
    Return (table_name, error_message). error_message None if OK.
    """
    if target == "private":
        if "username" not in session:
            return {None, "Please log in"}
        table_name = sanitize_table_name("personal_collection_" + session["username"])
        return {table_name, None}
    elif target == "global":
        return {"public_digimon_cards", None}
    else:
        return {None, f"Incorrect table name, {target} given"}

def get_card_list_from_table(table_name: str) -> list:
    """
    Return a list of cards from the specified table.
    Each card is represented as a dictionary with keys: id, name, card_number, rarity.
    Returns an empty list if the table does not exist or on error.
    """
    table_name = sanitize_table_name(table_name)
    if not table_name:
        raise ValueError("Invalid table name")
    try:
        sql = f"SELECT id, name, card_number, rarity FROM `{table_name}` ORDER BY card_number"
        rows = db.query(sql)
        return [dict(row) for row in rows]
    except Exception:
        return []

def get_card_number_from_table(table_name: str) -> int:
    """
    Return the number of cards in the specified table.
    Returns 0 if the table does not exist or on error.
    """
    table_name = sanitize_table_name(table_name)
    if not table_name:
        raise ValueError("Invalid table name")
    try:
        sql = f"SELECT COUNT(*) as count FROM `{table_name}`"
        rows = db.query(sql)
        return rows[0]["count"] if rows else 0
    except Exception:
        return 0

def get_latest_card_from_table(table_name: str) -> str | None:
    """
    Return the name of the latest card added to the specified table.
    Returns None if the table does not exist, is empty, or on error.
    """
    table_name = sanitize_table_name(table_name)
    if not table_name:
        raise ValueError("Invalid table name")
    try:
        sql = f"SELECT name FROM `{table_name}` ORDER BY id DESC LIMIT 1"
        rows = db.query(sql)
        return rows[0]["name"] if rows else None
    except Exception:
        return None

def add_card_to_table(table_name: str, name: str, card_number: str, rarity: str) -> None:
    """
    Add a card to the specified table.
    Raises sqlite3.Error if insertion fails.
    """
    table_name = sanitize_table_name(table_name)
    if not table_name:
        raise ValueError("Invalid table name")
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
            (name, card_number, rarity)
        )

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

def edit_card_in_table(table_name: str, id_int: int, name: str, card_number: str, rarity: str) -> None:
    """
    Edit a card in the specified table by its primary key id.
    Takes the new name, card_number, and rarity as parameters.
    """
    table_name = sanitize_table_name(table_name)
    if not table_name:
        raise ValueError("Invalid table name")
    db.execute(
        f'UPDATE "{table_name}" SET name = ?, card_number = ?, rarity = ? WHERE id = ?',
        (name, card_number, rarity, id_int)
    )

def delete_card_from_table(table_name: str, id_int: int) -> None:
    """
    Delete a card from the specified table by its primary key id.
    """
    table_name = sanitize_table_name(table_name)
    if not table_name:
        raise ValueError("Invalid table name")
    db.execute(f'DELETE FROM "{table_name}" WHERE id = ?', [id_int])

def find_card_using_id(id, table_name):
    """
    Look up a card by its primary key id.
    Returns:
      - the card data if found
      - None if not found or on invalid input / error
    """
    table_name = sanitize_table_name(table_name)
    if not table_name:
        raise ValueError("Invalid table name")
    if not isinstance(id, int):
        return None
    try:
        sql = f"SELECT id, name, card_number, rarity FROM {table_name} WHERE id = ?"
        rows = db.query(sql, [id])
    except Exception:
        return None

    if not rows:
        return None

    return rows[0]

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

    return rows[0]["id"]
