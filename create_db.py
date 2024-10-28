import sqlite3

def create_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create citizens table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS citizens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        mobile TEXT UNIQUE,
        password TEXT
    )
    ''')

    # Create police table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS police (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        mobile TEXT UNIQUE,
        password TEXT
    )
    ''')

    # Create complaints table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        citizen_id INTEGER,
        mobile TEXT,
        location TEXT,
        crime_type TEXT,
        station TEXT,
        description TEXT,
        status TEXT,
        image TEXT,
        FOREIGN KEY (citizen_id) REFERENCES citizens (id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Database and tables created!")

if __name__ == "__main__":
    create_database()
