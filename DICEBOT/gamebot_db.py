import sqlite3

connection = sqlite3.connect('gamebot_db.db')
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS gamedata(
id int auto_increment primary_key,
playerid int, 
balance int,              
wins int,
losses int,
tie int,
status int,
value int,
rid int 
)""")


connection.commit()
connection.close()