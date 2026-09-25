# tikawe_DigimonTcgDatabase
A database for storing information about Digimon cards and their classifications.

The application accesses a database containing cards from Digimon Card Game. The cards as database entities have a couple attributes such as rarity, level and color. There exists a general table of cards accessible to all users, which contains a broad list of cards.

Users can also store and browse their virtual collection of cards in the database as an another table. In future versions of the app their collection can be added to and cards can be removed from the collection.

With the finished product user might be able to have the application output their collection as a CSV file which they can copy/paste to a different application such as digimoncarddev.com.

The application contains a personal page for an user showing their current collection. Other users' collections can be viewed, but not edited.

Users will be able to browse the collections of other users, but only edit their own collection.

Admin level users should be able to edit the entire database.

Before starting the application, the user must create a file named database.db in the database in the project's root directory. This is done using sqlite3 in the following way:

$ sqlite3 database.db
sqlite> CREATE TABLE cards (id INTEGER PRIMARY KEY, name TEXT);
sqlite> .quit

You can start the application in a virtual environment by running the following commands in the project root:

$ source venv/bin/activate $ pip install flask $ flask run

The application will then run on port 5000.