import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()

cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY,
        email TEXT,
        username TEXT,
        point INTEGER,
        matches INTEGER,
        last_match DATE,
        created DATE,
        leaderboard BOOLEAN,
        description TEXT,
        active BOOLEAN
    )''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS games (
        uid TEXT PRIMARY KEY,
        round INTEGER,
        points INTEGER
    )''')

conn.commit()
conn.close()