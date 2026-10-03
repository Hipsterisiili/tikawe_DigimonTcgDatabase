import db

def add_comment(db, commenter_id, receiver_id, comment_text):
    """
    Add a comment to the comments table.
    """
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


