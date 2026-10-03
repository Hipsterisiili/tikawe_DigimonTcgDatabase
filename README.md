# tikawe_DigimonTcgDatabase

A database-backed Flask application for storing information about Digimon cards and user collections.

## Overview

The app stores cards from the Digimon Card Game. Each card has attributes (e.g. rarity, level, color). 
App contains a database containing 4 tables:
- Public collection `cards` 
- Personal collection for each user `personal_table_{username}`. 
- Table containing user information `users`
- Table containing comments left in collections by users


## Features

- Somewhat secure password management
- Global catalog which every logged-in user can view and edit
    - User can edit the card's information
    - User can delete a card from catalog
    - User can directly add cards from this catalog to their collections
- Personal catalog, which only their owner can edit
    - User can edit the card's information
    - User can delete a card from catalog
- User catalog for browsing other users and their collections
    - Contains a link to viewing ach user's collection
- Commenting on other users' collections.
    - Only the collection's owner may read these comments.
    - The collection's owner may delete these comments


## Planned features

- Searching for users
- Searching for cards
- Exporting a personal collection as CSV for use in other apps.
- Images for cards (If there is time for implementing)
- Drafting from a pre-built collection (likely after the course has ended)


## Minimal requirements

```bash
$ sudo apt install sqlite3
$ pip install flask
```

## Database setup

Generate the database for the application using the file schema.sql in the project's root using the command:
```bash
$ sqlite3 database.db < schema.sql
```

## Starting the application

You can start the application in a virtual environment by running the following commands in the project root:

```bash
$ source venv/bin/activate 
$ pip install flask 
$ flask run
```

The application will run on port 5000.