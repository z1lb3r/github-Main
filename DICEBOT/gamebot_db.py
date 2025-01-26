import sqlite3

# Establish a connection to the SQLite database
connection = sqlite3.connect('gamebot_db.db')
cursor = connection.cursor()

# Create the `gamedata` table
cursor.execute("""
CREATE TABLE IF NOT EXISTS gamedata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playerid INTEGER UNIQUE,          -- Telegram user ID (unique identifier)
    wins INTEGER DEFAULT 0,           -- Number of wins
    losses INTEGER DEFAULT 0,         -- Number of losses
    tie INTEGER DEFAULT 0,            -- Number of ties
    status INTEGER DEFAULT 0,         -- Player status (e.g., 0 = not searching, 1 = searching for rival)
    value INTEGER DEFAULT 0,          -- Temporary storage for dice roll values
    rid INTEGER DEFAULT NULL,         -- Rival player ID (NULL if no rival found)
    balance REAL DEFAULT 100.0        -- User's balance in game points
)
""")

# Create the `pending_deposits` table
cursor.execute("""
CREATE TABLE IF NOT EXISTS pending_deposits (
    tx_id TEXT PRIMARY KEY,           -- Transaction ID from the blockchain
    playerid INTEGER,                 -- Telegram user ID of the player
    amount REAL,                      -- Amount of USDT deposited
    status TEXT DEFAULT 'pending',    -- Current status of the deposit ('pending')
    timestamp TEXT                    -- Timestamp when the deposit was initiated
)
""")

# Create the `processed_deposits` table
cursor.execute("""
CREATE TABLE IF NOT EXISTS processed_deposits (
    tx_id TEXT PRIMARY KEY,           -- Transaction ID from the blockchain
    playerid INTEGER,                 -- Telegram user ID of the player
    amount REAL,                      -- Amount of USDT deposited
    timestamp TEXT                    -- Timestamp when the deposit was successfully processed
)
""")

# Create the `withdrawal_requests` table
cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawal_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playerid INTEGER,                 -- Telegram user ID of the player
    amount REAL,                      -- Amount of USDT the player wants to withdraw
    wallet_address TEXT,              -- TRC20 wallet address for the withdrawal
    status TEXT DEFAULT 'pending',    -- Current status of the withdrawal ('pending', 'approved', 'rejected')
    timestamp TEXT                    -- Timestamp when the withdrawal request was made
)
""")

# Create the `processed_withdrawals` table
cursor.execute("""
CREATE TABLE IF NOT EXISTS processed_withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playerid INTEGER,                 -- Telegram user ID of the player
    amount REAL,                      -- Amount of USDT withdrawn
    wallet_address TEXT,              -- TRC20 wallet address where the withdrawal was sent
    timestamp TEXT                    -- Timestamp when the withdrawal was successfully processed
)
""")

# Commit changes and close the connection
connection.commit()
connection.close()