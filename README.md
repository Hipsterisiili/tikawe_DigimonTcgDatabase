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
    - Only one card can exist with the same card_id
- Personal catalog, which only their owner can edit
    - User can edit the card's information
    - User can delete a card from catalog
    - Possible to have multiple cards with same card_id
- User catalog for browsing other users and their collections
    - Contains a link to viewing ach user's collection
- Commenting on other users' collections.
    - Only the collection's owner may read these comments.
    - The collection's owner may delete these comments

## What an user needs to know about a Digimon card?

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
- A card has multiple other identifiers such as level, type, color and cost, but those are not taken into account in this application: Reason for this is that I am intending on later building a boster drafting system within this application and the a booster draft's output only takes card's rarity into account.

## Planned features

- Searching for users
- Searching for cards
- When multiple cards with same card_id are added, all values other than id (primary key) should be identical
- Recognize and stack multiple instances of same card in personal collection
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