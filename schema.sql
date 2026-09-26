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