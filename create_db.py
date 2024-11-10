# create_db.py
import sqlite3

def create_db():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    # Create citizens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS citizens (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            mobile TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_image TEXT
        )
    ''')

    # Create police table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS police (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            mobile TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            department TEXT NOT NULL,
            profile_image TEXT
        )
    ''')

    # Create complaints table with police_id foreign key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY,
            citizen_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            image TEXT,
            department TEXT NOT NULL,
            police_id INTEGER,  -- Add this line to store assigned police officer ID
            FOREIGN KEY (citizen_id) REFERENCES citizens(id),
            FOREIGN KEY (police_id) REFERENCES police(id)
        )
    ''')

    # Create admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    connection.commit()
    connection.close()

if __name__ == '__main__':
    create_db()
