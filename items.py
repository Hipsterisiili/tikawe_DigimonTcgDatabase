from curses import flash
import re
from flask import flash
from constants import ALLOWED_RARITIES, ALLOWED_SETS
import db

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

from typing import Tuple, Optional
import users

def table_for_target(target: str, session) -> Tuple[Optional[int], Optional[str]]:
    """
    Return (owner_id, error_message). owner_id is None for public table, or an int user id for private.
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
        card_name = sanitize_card_name(card_name)
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

def get_card_count(owner_id: Optional[int], card_set: str | None = None) -> int:
    """
    Find out how many cards are in table and return the result as int.
    If a set is given as a parameter, count only cards with a matching set
    If owner_id is None -> count public_digimon_cards.
    If owner_id is int -> count private_digimon_cards WHERE owner_id = ?
    """
    if owner_id is None:
        table = "public_digimon_cards"
        if card_set and card_set != "all":
            sql = f'SELECT COUNT(*) AS cnt FROM "{table}" WHERE card_number LIKE ?'
            rows = db.query(sql, [f"{card_set}-%"])
        else:
            sql = f'SELECT COUNT(*) AS cnt FROM "{table}"'
            rows = db.query(sql)
    else:
        table = "private_digimon_cards"
        if card_set and card_set != "all":
            sql = f'SELECT COUNT(*) AS cnt FROM "{table}" WHERE owner_id = ? AND card_number LIKE ?'
            rows = db.query(sql, [owner_id, f"{card_set}-%"])
        else:
            sql = f'SELECT COUNT(*) AS cnt FROM "{table}" WHERE owner_id = ?'
            rows = db.query(sql, [owner_id])

    return int(rows[0]["cnt"]) if rows else 0


def get_card_list(owner_id: Optional[int], limit: int = 100, offset: int = 0, card_set: str | None = None) -> list:
    """
    Return a list of cards as dicts from the requested table.
    If owner_id is None, returns contents of public table
    Otherwise returns contents pf private table filtered by owner_id.
    Each card is represented as a dictionary with keys: id, name, card_number, rarity.
    Returns an empty list if the table does not exist or on error.
    """
    try:
        if owner_id is None:
            table = "public_digimon_cards"
            if card_set and card_set != "all":
                sql = f'SELECT id, name, card_number, rarity FROM "{table}" WHERE card_number LIKE ? ORDER BY id LIMIT ? OFFSET ?'
                rows = db.query(sql, [f"{card_set}-%", limit, offset])
            else:
                sql = f'SELECT id, name, card_number, rarity FROM "{table}" ORDER BY id LIMIT ? OFFSET ?'
                rows = db.query(sql, [limit, offset])
        else:
            table = "private_digimon_cards"
            if card_set and card_set != "all":
                sql = f'SELECT id, name, card_number, rarity FROM "{table}" WHERE owner_id = ? AND card_number LIKE ? ORDER BY id LIMIT ? OFFSET ?'
                rows = db.query(sql, [owner_id, f"{card_set}-%", limit, offset])
            else:
                sql = f'SELECT id, name, card_number, rarity FROM "{table}" WHERE owner_id = ? ORDER BY id LIMIT ? OFFSET ?'
                rows = db.query(sql, [owner_id, limit, offset])

        return [dict(r) for r in rows] if rows else []
    except Exception as e:
        print("get_card_list error:", e)
        return []
    
def get_card_number_from_table(owner_id: Optional[int]) -> int:
    """
    Return the number of cards for the given owner.
    - owner_id is None -> count public_digimon_cards
    - owner_id is an int -> count private_digimon_cards WHERE owner_id = ?
    Returns 0 if the table does not exist or on error.
    """
    try:
        if owner_id is None:
            sql = 'SELECT COUNT(*) AS count FROM "public_digimon_cards"'
            rows = db.query(sql)
        else:
            sql = 'SELECT COUNT(*) AS count FROM "private_digimon_cards" WHERE owner_id = ?'
            rows = db.query(sql, [owner_id])

        return int(rows[0]["count"]) if rows else 0
    except Exception:
        return 0

def get_latest_card(owner_id: Optional[int]) -> str | None:
    try:
        if owner_id is None:
            sql = 'SELECT name FROM "public_digimon_cards" ORDER BY id DESC LIMIT 1'
            rows = db.query(sql)
        else:
            sql = 'SELECT name FROM "private_digimon_cards" WHERE owner_id = ? ORDER BY id DESC LIMIT 1'
            rows = db.query(sql, [owner_id])
        return rows[0]["name"] if rows else None
    except Exception:
        return None


def add_card(owner_id: Optional[int], name: str, card_number: str, rarity: str) -> None:
    """
    Insert into public table if owner_id is None
    Insert into private table if owner_id is provided as parameter.
    """
    if owner_id is None:
        db.execute(
            'CREATE TABLE IF NOT EXISTS public_digimon_cards ('
            'id INTEGER PRIMARY KEY, '
            'name TEXT NOT NULL, '
            'card_number TEXT, '
            "rarity TEXT CHECK (rarity IS NULL OR rarity IN ('C','U','R','UR','SEC','P','SR'))"
            ')'
        )
        db.execute(
            'INSERT INTO public_digimon_cards (name, card_number, rarity) VALUES (?, ?, ?)',
            (name, card_number, rarity)
        )
    else:
        db.execute(
            'CREATE TABLE IF NOT EXISTS private_digimon_cards ('
            'id INTEGER PRIMARY KEY, '
            'name TEXT NOT NULL, '
            'card_number TEXT, '
            "rarity TEXT CHECK (rarity IS NULL OR rarity IN ('C','U','R','UR','SEC','P','SR')), "
            'owner_id INTEGER NOT NULL, '
            'FOREIGN KEY(owner_id) REFERENCES users(id)'
            ')'
        )
        db.execute(
            'INSERT INTO private_digimon_cards (name, card_number, rarity, owner_id) VALUES (?, ?, ?, ?)',
            (name, card_number, rarity, owner_id)
        )


def edit_card(id_int: int, owner_id: Optional[int], name: str, card_number: str, rarity: str) -> None:
    """
    Edit a card in the specified table.
    Card is located using the primary key id given as parameter.
    Takes the new name, card_number, and rarity as parameters.
    If owner_id is None, edits public table row with id
    If owner_id exists, edits private table row with id AND owner_id (so user can't edit another user's card)
    """
    if owner_id is None:
        db.execute('UPDATE public_digimon_cards SET name = ?, card_number = ?, rarity = ? WHERE id = ?',
                   (name, card_number, rarity, id_int))
    else:
        db.execute('UPDATE private_digimon_cards SET name = ?, card_number = ?, rarity = ? WHERE id = ? AND owner_id = ?',
                   (name, card_number, rarity, id_int, owner_id))


def delete_card(id_int: int, owner_id: Optional[int]) -> None:
    """
    Delete a card from the specified table by its primary key id.
    If owner_id is None, deletes from public table row with id matching parameter id_int.
    If owner_id exists, deletes from private table row with id AND owner_id.
    """
    if owner_id is None:
        db.execute('DELETE FROM public_digimon_cards WHERE id = ?', [id_int])
    else:
        db.execute('DELETE FROM private_digimon_cards WHERE id = ?', [id_int])


def find_card_by_id(id_int: int, owner_id: Optional[int]):
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
            sql = 'SELECT id, name, card_number, rarity FROM public_digimon_cards WHERE id = ?'
            rows = db.query(sql, [id_int])
        else:
            sql = 'SELECT id, name, card_number, rarity FROM private_digimon_cards WHERE id = ? AND owner_id = ?'
            rows = db.query(sql, [id_int, owner_id])
    except Exception:
        return None
    return rows[0] if rows else None


def find_card_id_by_card_number(card_number: str, owner_id: Optional[int]) -> int:
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
            rows = db.query('SELECT id FROM public_digimon_cards WHERE card_number = ? LIMIT 1', (card_number,))
        else:
            rows = db.query('SELECT id FROM private_digimon_cards WHERE owner_id = ? AND card_number = ? LIMIT 1', (owner_id, card_number))
    except Exception:
        return 0
    if not rows:
        return 0
    return rows[0]['id']

