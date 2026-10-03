import re
import db

def _sanitize_table_name(name: str) -> str | None:
    """
    Turn an arbitrary username into a safe table identifier used for per-user tables.
    Returns the sanitized name (e.g. personal_collection_john_doe) or None if invalid.
    """
    if not isinstance(name, str):
        return None
    # replace non-word characters with underscore
    s = re.sub(r'\W+', '_', name).strip()
    # must not start with a digit, and must match allowed pattern
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', s):
        return s
    return None


def insert_user(username: str, password_hash: str) -> None:
    """
    Insert a new user into users table.
    Raises sqlite3.IntegrityError if username already exists.
    """
    sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
    db.execute(sql, (username, password_hash))


def create_personal_table_for(username: str) -> str:
    """
    Create the per-user personal collection table.
    Returns the actual table name used.
    Raises ValueError if the username cannot be sanitized.
    """
    base = "personal_collection_" + username
    table_name = _sanitize_table_name(base)
    if not table_name:
        raise ValueError("Invalid username for table name")

    create_sql = (
        f'CREATE TABLE IF NOT EXISTS "{table_name}" ('
        'id INTEGER PRIMARY KEY, '
        'name TEXT NOT NULL, '
        'card_number TEXT, '
        f'rarity TEXT CHECK (rarity IS NULL OR rarity IN (\'C\',\'U\',\'R\',\'UR\',\'SEC\',\'P\',\'SR\'))'
        ')'
    )
    db.execute(create_sql)
    return table_name

def get_password_hash(username):
    """Return the stored password hash for username or None if not found."""
    sql = "SELECT password_hash FROM users WHERE username = ?"
    rows = db.query(sql, [username])
    return rows[0]["password_hash"] if rows else None

def get_all_users():
    """Return a list of all users with their username, created_at, and is_admin."""
    sql = "SELECT username, created_at, is_admin FROM users ORDER BY username"
    return db.query(sql)

def get_user_by_username(username):
    sql = "SELECT id, username FROM users WHERE username = ?"
    rows = db.query(sql, [username])
    return rows[0] if rows else None

def add_comment(db, commenter_id, receiver_id, comment_text):
    sql = """INSERT INTO comments (commenter_id, receiver_id, comment_text)
             VALUES (?, ?, ?)"""
    db.execute(sql, [commenter_id, receiver_id, comment_text])

def get_comment_list_using_receiver_name(receiver: str) -> list:
    """
    Return a list of comments for the specified receiver_id.
    Each comment is represented as a dictionary with keys: comment_text, commenter_id, created_at.
    Returns an empty list if no comments are found or on error.
    """
    try:
        sql = f"SELECT comment_text, commenter_id, created_at FROM comments WHERE receiver_id = (SELECT id FROM users WHERE username = ?) ORDER BY created_at DESC"
        rows = db.query(sql, [receiver])
        return [dict(row) for row in rows]
    except Exception:
        return []
