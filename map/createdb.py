import sqlite3
conn = sqlite3.connect('map.db')

c = conn.cursor()

c.execute('CREATE TABLE users (id INTEGER PRIMARY KEY NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, display_name TEXT DEFAULT unknown, icon TEXT)')

conn.commit()

conn.close()