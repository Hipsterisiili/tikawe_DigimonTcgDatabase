from flask import session, flash
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
        sql = "SELECT c.comment_text, u.username AS commenter_username, c.created_at FROM comments c JOIN users u ON c.commenter_id = u.id WHERE c.receiver_id = ( SELECT id FROM users WHERE username = ? ) ORDER BY c.created_at DESC " 
        rows = db.query(sql, [receiver]) 
        return [dict(row) for row in rows] 
    except Exception: return []

def delete_comment(comment_id: int) -> None:
    """
    Delete a comment from the comments table by its ID.
    If comment receiver was not logged in, deleting fails and a flash message is shown.
    """
    receiver_username = db.query("SELECT u.username FROM comments c JOIN users u ON c.receiver_id = u.id WHERE c.id = ?", [comment_id])
    if not receiver_username == session.get("username"):
        flash("You do not have permission to delete this comment.")
    else:
        sql = "DELETE FROM comments WHERE id = ?"
        db.execute(sql, [comment_id])
