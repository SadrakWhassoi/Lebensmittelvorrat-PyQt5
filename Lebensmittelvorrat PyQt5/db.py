import sqlite3

DB_NAME = "lebensmittel.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS lebensmittel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            kategorie TEXT,
            menge REAL,
            einheit TEXT,
            lagerort TEXT,
            geöffnet INTEGER,
            mhd TEXT,
            eingelagert TEXT,
            bemerkungen TEXT
        )
    ''')
    conn.commit()
    conn.close()

def fetch_all():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM lebensmittel")
    rows = c.fetchall()
    conn.close()
    return rows

def add_entry(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO lebensmittel (name, kategorie, menge, einheit, lagerort, geöffnet, mhd, eingelagert, bemerkungen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()

def update_menge(id, delta):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE lebensmittel SET menge = menge + ? WHERE id = ?", (delta, id))
    conn.commit()
    conn.close()

def delete_entry(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM lebensmittel WHERE id = ?", (id,))
    conn.commit()
    conn.close()