from curses import flash
import re
import random
import sqlite3
from flask import request
import db

def find_card_using_id(id, table_name, db=db):
    """
    Look up a card by its primary key id.
    Returns:
      - the card data if found
      - None if not found or on invalid input / error
    """
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

def sanitize_table_name(name: str) -> str:
    """
    Return a safe table name (same scheme used when creating per-user tables),
    or None if invalid. Allows letters, digits and underscores, and no leading digit.
    """
    print("Sanitizing")
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

def edit_card_in_table(table_name: str, id_int: int, name: str, card_number: str, rarity: str) -> None:
    """
    Edit a card in the specified table by its primary key id.
    Raises sqlite3.Error if update fails.
    """
    db.execute(
        f'UPDATE "{table_name}" SET name = ?, card_number = ?, rarity = ? WHERE id = ?',
        (name, card_number, rarity, id_int)
    )

def delete_card_from_table(table_name: str, id_int: int) -> None:
    """
    Delete a card from the specified table by its primary key id.
    Raises sqlite3.Error if deletion fails.
    """
    db.execute(f'DELETE FROM "{table_name}" WHERE id = ?', [id_int])
