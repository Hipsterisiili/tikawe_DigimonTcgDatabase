# tikawe_DigimonTcgDatabase

A database-backed Flask application for storing information about Digimon cards and user collections.

## Overview

The app stores cards from the Digimon Card Game. Each card has attributes (e.g. rarity, level, color). 
App contains a database containing 4 tables:
- Public collection `cards`.
- Personal collection for each user `personal_table_{username}`.
- Table containing user information `users`.
- Table containing comments left in collections by users.

## Features

- Somewhat secure password management
- Global catalog which every logged-in user can view and edit
    - Admin can edit the card's information
    - Admin can delete a card from catalog
    - Any user can directly add cards from this catalog to their collections
    - Only one card can exist with the same card_id
- Personal catalog, which only their owner can edit
    - User can edit the card's information
    - User can delete a card from catalog
    - Possible to have multiple cards with same card_id
- User catalog for browsing other users and their collections
    - Contains a link to viewing ach user's collection
    - User can search for other users by username
- Commenting on other users' collections.
    - Only the collection's owner may read these comments.
    - The collection's owner may delete these comments.

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

- Searching for cards.
- Adding a publicly visible comment to own collection. (not very relevant)
- When multiple cards with same card_id are added, all values other than id (primary key) should be identical.
- Recognize and stack multiple instances of same card in personal collection. (If there is time for implementing)
- Images for cards (If there is time for implementing)
- Exporting a personal collection as CSV for use in other apps. (likely after the course has ended)
- Importing a collection as CSV from other apps. (likely after the course has ended)
- Drafting from a pre-built collection (likely after the course has ended)


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

## Starting the application

You can start the application in a virtual environment by running the following commands in the project root:

```bash
 python3 -m venv venv
 source venv/bin/activate 
 pip install flask 
 flask run
```

The application will run on port 5000.