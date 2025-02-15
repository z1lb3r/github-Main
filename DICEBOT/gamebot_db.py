import sqlite3

connection = sqlite3.connect('gamebot_db.db')
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS gamedata(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playerid INTEGER UNIQUE,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    tie INTEGER DEFAULT 0,
    status INTEGER DEFAULT 0,
    value INTEGER DEFAULT 0,
    rid INTEGER,
    balance REAL DEFAULT 0
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS deposits(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playerid INTEGER,
    amount REAL,
    sender_address TEXT,
    status TEXT,
    txid TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS withdrawals(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playerid INTEGER,
    amount REAL,
    recipient_address TEXT,
    status TEXT,
    txid TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)""")

connection.commit()
connection.close()
