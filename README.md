# tikawe_DigimonTcgDatabase

A database-backed Flask application for storing information about Digimon cards and user collections.

## Overview

The app stores cards from the Digimon Card Game. Each card has attributes (e.g. rarity, level, color). 
App contains a database containing 4 tables:
- Table containing user information `users`.
    - id (INTEGER, primary key)
    - username (TEXT, user's username)
    - password_hash (TEXT, user's password securely hashed)
    - created_at (DATETIME, the exact time when the user was registered)
    - is_admin (INTEGER, 0 representing regular user, 1 representing admin level user)
- Public collection `public_digimon_cards`.
    - id (INTEGER, primary key)
    - name (TEXT, card's name)
    - card_number (TEXT, The game's own identifier for indexing cards)
    - rarity (TEXT, Whether the card is common, umcommon, rare, etc.)
- Personal collections for each user in table `private_digimon_cards`.
    - id (INTEGER, primary key)
    - name (TEXT)
    - card_number (TEXT)
    - rarity (TEXT)
    - owner_id (INTEGER, references users(id))
- Table `comments` containing comments left in collections by users.
    - id (INTEGER, primary key)
    - commenter_id (INT, references users(id), The comment's writer)
    - receiverer_id (INT, references users(id, The comment's receiver))
    - comment_text (TEXT, contents of the comment)
    - created_at (DATETIME, the exact time when the comment was left)

## Features

- Somewhat secure password management
- Global catalog
    - **Everyone** can view it
    - **Admin** can edit cards in it
    - **Admin** can delete a card from catalog
    - **Any logged in user** can directly add cards from this catalog to their personal collections
    - Cards may be viewed all at once or one set at a time
    - Only one card can exist with the same card_id
- Personal catalog
    - **Catalog's owner** can edit cards in it
    - **Catalog's owner** can edit the card's information
    - **Catalog's owner** can delete a card from catalog
    - **Everyone** can view it through user list
    - Possible to have multiple cards with same card_id
- User catalog for browsing other users and their collections
    - **Everyone** can view it with no limitations
    - Contains a link to viewing each user's collection
    - When **a logged in user** want's to view their own collection, their personal collection is opened in an editable view.
    - **Everyone** can search for other users by username
- **Any logged in user** may comment on other users' collections.
    - **Collection's owner** may read these comments.
    - **Collection's owner** may delete these comments.

## What a user needs to know about a Digimon card?

- Cards are identified using a card id consisting of set id and set number 
    - BT1-001 refers to a card number 001 from Base set 1
    - ST12-021 refers to a card number 021 from Starter deck 21
    - P-94 refers to the 94:th promo card 
- Card has a rarity which is one of following:
    - C (Common)
    - U (Uncommon)
    - R (Rare)
    - SR (Super Rare)
    - UR (Ultra Rare)
    - SEC (Secret Rare)
- A card has multiple other identifiers such as level, type, color and cost, but those are not taken into account in this application: Reason for this is that I am intending on later building a booster drafting system within this application and the a booster draft's output only takes card's rarity into account.

## Planned features

- Card id field should only accepts numbers even before submit is pressed. 
- Adding a publicly visible comment to own collection. (not very relevant)
- When multiple cards with same card_id are added, all values other than id (primary key) should be identical.
- Recognize and stack multiple instances of same card in personal collection. (After the course)
- Images for cards (After the course)
- Exporting a personal collection as CSV for use in other apps. (After the course)
- Importing a collection as CSV from other apps. (After the course)
- Drafting from a pre-built collection (After the course)

## Known issues

- Inputting invalid card name length results to error screen instead of an error message and redirect. Likely fixed by returning a possible error message along with name from items/is_card_name_valid.
- No validation of characters in card names implemented yet.
- Card id suffix can be any integer, should only take numbers between 1-999


## Minimal requirements

```bash
 sudo apt install sqlite3
 pip install flask
```

## Database setup

Generate the database for the application using the file schema.sql in the project's root using the command:
```bash
 sqlite3 database.db < schema.sql
```

### Optional:

Generate a few cards to the public collection by running:
```bash
sqlite3 database.db < dummy_content_script.sql
```

The first 3 base sets (BT1, BT2 and BT3) can be added in the public collection ry running
```bash
sqlite3 database.db < sets/BT1.sql
sqlite3 database.db < sets/BT2.sql
sqlite3 database.db < sets/BT3.sql
```

## Starting the application

You can start the application in a virtual environment by running the following commands in the project root:

```bash
 python3 -m venv venv
 source venv/bin/activate 
 pip install flask 
 flask run
```

The application will run on port 5000.