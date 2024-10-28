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
            password TEXT NOT NULL
        )
    ''')

    # Create police table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS police (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            mobile TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            department TEXT NOT NULL
        )
    ''')

    # Create complaints table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            image TEXT,
            department TEXT NOT NULL,
            FOREIGN KEY (id) REFERENCES citizens(id)
        )
    ''')

    connection.commit()
    connection.close()

if __name__ == '__main__':
    create_db()
