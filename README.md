# tikawe_DigimonTcgDatabase

A database-backed Flask application for storing information about Digimon cards and user collections.

## Overview

The app stores cards from the Digimon Card Game. Each card has attributes (e.g. rarity, level, color). There is a global `cards` table accessible to all users and each user has a personal collection stored as a separate table (current design). Users can view other users' collections (read-only) and view their own (editable). Admin users can edit the entire database.

Planned features include adding/removing cards from personal collections and exporting a personal collection as CSV.

## Features

- Global `cards` table (catalog) which every user can view, add to and remove from
- Per-user personal collection tables
- View your own collection and (planned) other users' collections
- Add and remove cards from personal collection
- Add/remove cards from personal collections
- (Planned) Export personal collections as CSV
- (Planned) Admin-level editing

## Database setup

Create the SQLite database file `database.db` in the project root and create the initial `cards` table:

```bash
sqlite3 database.db
```

Inside the sqlite prompt:

```bash
sqlite> CREATE TABLE cards (id INTEGER PRIMARY KEY, name TEXT);

sqlite> .quit
```

## Starting the application

You can start the application in a virtual environment by running the following commands in the project root:

```bash
$ source venv/bin/activate $ pip install flask $ flask run
```

The application will then run on port 5000.