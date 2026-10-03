CREATE TABLE public_digimon_cards (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  card_number TEXT NOT NULL UNIQUE,
  rarity TEXT CHECK (rarity IS NULL OR rarity IN ('C','U','R','UR','SEC','P','SR'))
);

CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_admin INTEGER DEFAULT 0
)

CREATE TABLE comments ( 
  id INTEGER PRIMARY KEY, 
  commenter_id INTEGER NOT NULL, 
  receiver_id INTEGER NOT NULL, 
  comment_text TEXT NOT NULL, 
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
  FOREIGN KEY (commenter_id) 
  REFERENCES users(id) 
  ON DELETE CASCADE, 
  FOREIGN KEY (receiver_id) 
  REFERENCES users(id) 
  ON DELETE CASCADE );

CREATE INDEX idx_comments_receiver_id 
  ON comments(receiver_id); 
  
CREATE INDEX idx_comments_commenter_id 
  ON comments(commenter_id);