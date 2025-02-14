import sqlite3

connection = sqlite3.connect('gamebot_db.db')
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS gamedata(
id INTEGER PRIMARY KEY AUTOINCREMENT,
playerid int,              
wins int,
losses int,
tie int,
status int,
value int,
rid int,
balance int
)""")


connection.commit()
connection.close()
