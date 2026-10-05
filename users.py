import re
import db
from werkzeug.security import check_password_hash

_USERNAME_RE = re.compile(r'^[A-Za-z0-9_.-]+$')

def validate_new_account_input( username: str, password1: str, password2: str ) -> tuple[str, str]:
    """ Validate username and passwords for account creation.
    Returns (normalized_username, error_message).
    - normalized_username is username.strip() (may be empty string if input was empty)
    - error_message is None when validation passed, otherwise a human-readable
    string (possibly with multiple lines) describing the problem(s).
    """
    errors = []

    if not username:
        errors.append("Username is required.")
    else:
        if len(username) < 3 or len(username) > 30:
            errors.append("Your username length must be between 3 and 30 characters.")
        if not _USERNAME_RE.fullmatch(username):
            errors.append("Username contains invalid characters (allowed: letters, numbers, _, ., -).")

    if not password1:
        errors.append("Password is required.")
    else:
        if len(password1) < 3 or len(password1) > 30:
            errors.append("Your password length must be between 3 and 30 characters.")
        if password1 != password2:
            errors.append("Passwords don't match.")

    err = "\n".join(errors)
    return username, err or None


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

def check_login(username, password):
    sql = "SELECT id, password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])

    if len(result) == 1:
        user_id, password_hash = result[0]
        if check_password_hash(password_hash, password):
            return user_id

    return None

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

