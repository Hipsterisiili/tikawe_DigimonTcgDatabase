# tikawe_DigimonTcgDatabase

A database-backed Flask application for storing information about Digimon cards and user collections.

## Overview

The app stores cards from the Digimon Card Game. Each card has attributes (e.g. rarity, level, color). 
App contains a database containing 4 tables:
- Table containing user information `users`.
    - **id** (INTEGER, primary key)
    - **username** (TEXT, user's username)
    - **password_hash** (TEXT, user's password securely hashed)
    - **created_at** (DATETIME, the exact time when the user was registered)
    - **is_admin** (INTEGER, 0 representing regular user, 1 representing admin level user)
- Public collection `public_digimon_cards`.
    - **id** (INTEGER, primary key)
    - **name** (TEXT, card's name)
    - ***card_number** (TEXT, The game's own identifier for indexing cards)
    - **rarity** (TEXT, Whether the card is common, umcommon, rare, etc.)
- Personal collections for each user in table `private_digimon_cards`.
    - **id** (INTEGER, primary key)
    - **name** (TEXT)
    - **card_number** (TEXT)
    - **rarity** (TEXT)
    - **owner_id** (INTEGER, references users(id))
- Table `comments` containing comments left in collections by users.
    - **id** (INTEGER, primary key)
    - **commenter_id** (INT, references users(id), The comment's writer)
    - **receiverer_id** (INT, references users(id, The comment's receiver))
    - **comment_text** (TEXT, contents of the comment)
    - **created_at** (DATETIME, the exact time when the comment was left)
- Table `classes`, defining the available classifications that can be assigned to cards.
    - **id** (INTEGER, primary key)
    - **title** (TEXT, the classification category, in this case Condition or Favorite)
    - **value** (TEXT, the available value within that category)
        - Condition values include NM (Near Mint), LP (Lightly Played), MP (Moderately Played), HP (Heavily Played), and D (Damaged).
        - Favorite values include yes and no.
- Table `item_classes`, storing classifications assigned to individual cards in personal collections.
    - **id** (INTEGER, primary key)
    - **item_id** (INTEGER, references private_digimon_cards(id))
    - **title** (TEXT, the classification category, such as Condition or Favorite)
    - **value** (TEXT, the assigned value, such as NM or yes)

Each row in item_classes associates a classification with a particular card. A card may have a condition and a favorite status. If a condition has not been assigned, no Condition row is required. To view table creation, read `schema.sql`. 


## Features

- Somewhat secure user and password management
    - The first user that is registered in the app becomes **admin**.
- Global catalog:
    - **Everyone** can view it
    - **Admin** can edit cards in it
    - **Admin** can delete a card from catalog
    - **Any logged in user** can directly add cards from this catalog to their personal collections
    - Cards may be viewed all at once or one set at a time
    - Only one card can exist with the same card_id
- Personal catalog:
    - **Catalog's owner** can edit cards in it
    - **Catalog's owner** can edit the card's information
    - **Catalog's owner** can delete a card from catalog
    - **Catalog's owner** can favorite cards.
    - **Everyone** can view it through user list
    - **Everyone** can view favorite cards only
    - Possible to have multiple cards with same card_id
    - User's catalog is limited to only 100 cards!
    - A condition can be assigned and wieved by **Catalog's owner** in card in personal collection
        -> (NM = Near Mint, LP = Lightly Played, MP = Moderately Played, HP = Heavily Played, D = Damaged)
- User catalog:
    - **Everyone** can browse other users and their collections
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

- Adding a publicly visible comment to own collection. (After the course)
- When multiple cards with same card_id are added, all values other than id (primary key) should be identical. (After the course)
- Recognize and stack multiple instances of same card in personal collection. (After the course)
- Images for cards (After the course)
- Exporting a personal collection as CSV for use in other apps. (After the course)
- Importing a collection as CSV from other apps. (After the course)
- Drafting from a pre-built collection (After the course)

## Minimal requirements

```bash
 sudo apt install sqlite3
 pip install flask
```

## Database setup

Generate the database for the application using the file schema.sql in the project's root using the command:
```bash
 sqlite3 database.db < schema.sql
 sqlite3 database.db < init.sql
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

## pylint report

Running
```bash
pylint app.py users.py items.py comments.py constants.py
```
in project root yields this pylint raport:
```bash
************* Module app
app.py:433:0: R0911: Too many return statements (9/6) (too-many-return-statements)
************* Module items
items.py:146:0: R0913: Too many arguments (6/5) (too-many-arguments)
items.py:146:0: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)

------------------------------------------------------------------
Your code has been rated at 9.96/10
```

The too many return statements error felt a bit too heavy to refactor during the final course day.
Too many arguments error is not resolved to keep code easier to read and in my opinion 6 arguments is still manageable. 