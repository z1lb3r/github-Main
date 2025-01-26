import sqlite3


#   UPDATE BALANCE
async def update_balance(user_id:int, points:int):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("""
                   UPDATE gamedata
                   SET balance = balance + ?
                   WHERE playerid = ?
                   """,(points, user_id))
    connection.commit()
    connection.close()


#   GET BALANCE
async def get_balance(user_id:int):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("""
                   SELECT balance FROM gamedata
                   WHERE playerid = ?
                   """,(user_id,))
    row = cursor.fetchone()
    connection.commit()
    connection.close()
    return row[0] if row else None


#   RESET GAME STATE
async def reset_game_state(user_id: int, rival_id: int):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("""
                   UPDATE gamedata
                   SET status = 0, rid = NULL, value = 0
                   WHERE playerid IN (?,?)
                   """,(user_id, rival_id))
    connection.commit()
    connection.close()

#   UPDATE DICE VALUE
async def update_dice_value(*, user_id: int, dice_value: int):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("""
                UPDATE gamedata 
                SET value = ?
                WHERE playerid = ?  
                """,(dice_value, user_id))
    connection.commit()
    connection.close()


#   GET DICE VALUE
async def get_dice_value(*, user_id: int):
    connection = sqlite3.connect("gamebot_db.db")
    cursor = connection.cursor()
    cursor.execute("""
                   SELECT value FROM gamedata
                   WHERE playerid = ?
                   """, (user_id,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return row[0]
    return None


#   GET RIVAL ID
async def get_rival_id(*, user_id: int):
    connection = sqlite3.connect("gamebot_db.db")
    cursor = connection.cursor()
    cursor.execute("""
                   SELECT rid FROM gamedata
                   WHERE playerid =?
                   """,(user_id,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return row[0]
    return None


#   INCREMENT WIN
async def increment_win(*, user_id: int):
    connection = sqlite3.connect("gamebot_db.db")
    cursor = connection.cursor()
    cursor.execute("""
                   UPDATE gamedata
                   SET wins = COALESCE(wins, 0)+1
                   WHERE playerid = ? 
                   """,(user_id,))
    connection.commit()
    connection.close()


#   INCREMENT LOSSES
async def increment_losses(*, user_id: int):
    connection = sqlite3.connect("gamebot_db.db")
    cursor = connection.cursor()
    cursor.execute("""
                   UPDATE gamedata
                   SET losses = COALESCE(losses, 0)+1
                   WHERE playerid = ? 
                   """,(user_id,))
    connection.commit()
    connection.close()


#   INCREMENT TIE
async def increment_tie(*, user_id: int):
    connection = sqlite3.connect("gamebot_db.db")
    cursor = connection.cursor()
    cursor.execute("""
                   UPDATE gamedata
                   SET tie = COALESCE(tie, 0)+1
                   WHERE playerid = ? 
                   """,(user_id,))
    connection.commit()
    connection.close()


# INSERT NEW USER 
async def insert_user(*, id: int, id2: int): 
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("INSERT INTO gamedata(playerid, balance) SELECT ?,100  WHERE NOT EXISTS (SELECT 1 FROM gamedata WHERE playerid = ?)",(id, id2))
    connection.commit()
    connection.close() 


#   GET DATA
async def get_data():
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("SELECT status FROM gamedata")
    row = cursor.fetchone()
    connection.commit()
    connection.close()
    return row


#   CHECK VALUE COLUMN
async def check_value(*, id: int):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("""
                   SELECT value FROM gamedata
                   WHERE playerid = ?""",(id,))
    row = cursor.fetchone()
    connection.commit()
    connection.close()
    return row


#   START SEARCH
async def start_search(*, id: int, status: int):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("UPDATE gamedata SET status = ? WHERE playerid = ?",(status,id))
    connection.commit()
    connection.close()


#   SET BALANCE
async def set_balance(*, id: int, balance: int):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("UPDATE gamedata SET balance = ? WHERE playerid = ?",(balance,id))
    connection.commit()
    connection.close()    


#   GET STATUS  OF A SPECIFIC PLAYER
async def get_status_of_player(*, playerid: int):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("SELECT status FROM gamedata WHERE playerid =?", (playerid,))
    row = cursor.fetchone()
    connection.commit()
    connection.close()
    return row[0] if row else None


#   LOOKING FOR RIVAL
async def give_me_rival(*, id: int):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
     # Find the earliest player with status=1, excluding the current player
    cursor.execute("""
                   SELECT playerid FROM gamedata
                   WHERE status = 1 AND playerid != ?
                   ORDER BY playerid ASC
                   LIMIT 1
                   """,(id,))
    row = cursor.fetchone()

    if row is None:
        connection.close()
        return None
    matched_player = row[0]

    cursor.execute("""
    UPDATE gamedata
    SET status = 2, rid =? 
    WHERE playerid = ?
    """,(id, matched_player))


    connection.commit()
    connection.close()
    return matched_player


# Check if a specific deposit transaction has already been processed
async def is_deposit_processed(tx_id: str) -> bool:
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 1 FROM processed_deposits WHERE tx_id = ?
    """, (tx_id,))
    result = cursor.fetchone()
    connection.close()
    return result is not None


# Record a deposit as "pending" in the database
async def record_pending_deposit(tx_id: str, user_id: int, amount: float):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO pending_deposits (tx_id, user_id, amount)
        VALUES (?, ?, ?)
    """, (tx_id, user_id, amount))
    connection.commit()
    connection.close()


# Mark a deposit as "processed" after it has been added to the user's balance
async def mark_deposit_processed(tx_id: str):
    connection = sqlite3.connect('gamebot_db.db')
    cursor = connection.cursor()
    try:
        # Begin transaction to ensure atomicity
        cursor.execute("BEGIN TRANSACTION")
        
        # Move the transaction from pending_deposits to processed_deposits
        cursor.execute("""
            INSERT INTO processed_deposits (tx_id)
            SELECT tx_id FROM pending_deposits WHERE tx_id = ?
        """, (tx_id,))
        
        # Delete the transaction from pending_deposits
        cursor.execute("""
            DELETE FROM pending_deposits WHERE tx_id = ?
        """, (tx_id,))
        
        # Commit transaction
        connection.commit()
    except sqlite3.Error as e:
        # Rollback transaction on error
        connection.rollback()
        print(f"Error processing transaction {tx_id}: {e}")
    finally:
        connection.close()





