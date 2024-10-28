from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import uuid  # Import UUID library to generate unique case numbers

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Initialize the database
def init_db():
    conn = sqlite3.connect('crime_reporting.db')
    cursor = conn.cursor()

    # Users Table with roles (Citizen, Staff, Admin)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,          -- User roles (Citizen, Staff, Admin)
        department TEXT               -- Department for Staff users (e.g., Police, Statistics)
    )
    ''')

    # Crime Reports Table with status field
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crime_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number TEXT NOT NULL,
        description TEXT,
        reported_by TEXT,
        officer_in_charge TEXT,
        status TEXT DEFAULT 'Pending'
    )
    ''')

    # Crime Statistics Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crime_statistics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crime_type TEXT NOT NULL,
        count INTEGER
    )
    ''')

    conn.commit()
    conn.close()

# Route for Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('crime_reporting.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            session['role'] = user[3]
            session['department'] = user[4]
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password. Please try again.", "error")
    
    return render_template('login.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # Capture role from the form
        
        try:
            conn = sqlite3.connect('crime_reporting.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           (username, password, role))
            conn.commit()
            conn.close()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists. Choose a different one.", "error")
    
    return render_template('register.html')


# Citizen Crime Report Submission with automatic case number generation
@app.route('/report_crime', methods=['GET', 'POST'])
def report_crime():
    if 'role' in session and session['role'] == 'Citizen':
        if request.method == 'POST':
            case_number = str(uuid.uuid4())  # Generate unique case number
            description = request.form['description']
            reported_by = session['username']
            
            conn = sqlite3.connect('crime_reporting.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO crime_reports (case_number, description, reported_by, status) VALUES (?, ?, ?, 'Pending')",
                           (case_number, description, reported_by))
            conn.commit()
            conn.close()
            flash("Crime reported successfully.", "success")
            return redirect(url_for('dashboard'))
        return render_template('report_crime.html')
    else:
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))


# Police Staff - Add Crime Directly
@app.route('/add_crime', methods=['GET', 'POST'])
def add_crime():
    if 'role' in session and session['role'] == 'Staff' and session['department'] == 'Police':
        if request.method == 'POST':
            case_number = request.form['case_number']
            description = request.form['description']
            officer_in_charge = session['username']
            
            conn = sqlite3.connect('crime_reporting.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO crime_reports (case_number, description, officer_in_charge, status) VALUES (?, ?, ?, 'Pending')",
                           (case_number, description, officer_in_charge))
            conn.commit()
            conn.close()
            flash("Crime added successfully.", "success")
            return redirect(url_for('dashboard'))
        return render_template('add_crime.html')
    else:
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    
# Police Staff - Update Crime Details
@app.route('/update_crime/<int:crime_id>', methods=['GET', 'POST'])
def update_crime(crime_id):
    if 'role' in session and session['role'] == 'Police':
        conn = sqlite3.connect('crime_reporting.db')
        cursor = conn.cursor()
        
        # Fetch crime details for pre-filling the form
        if request.method == 'GET':
            cursor.execute("SELECT * FROM crime_reports WHERE id=?", (crime_id,))
            crime = cursor.fetchone()
            conn.close()
            return render_template('update_crime.html', crime=crime)
        
        # Update crime details on form submission
        elif request.method == 'POST':
            description = request.form['description']
            status = request.form['status']
            cursor.execute("UPDATE crime_reports SET description=?, status=? WHERE id=?",
                           (description, status, crime_id))
            conn.commit()
            conn.close()
            flash("Crime details updated successfully.", "success")
            return redirect(url_for('dashboard'))
    
    else:
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))


# Dashboard Route - Different views based on role
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    role = session['role']
    department = session.get('department')
    
    if role == 'Citizen':
        conn = sqlite3.connect('crime_reporting.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crime_reports WHERE reported_by=?", (session['username'],))
        reports = cursor.fetchall()
        conn.close()
        return render_template('dashboard.html', role=role, reports=reports)

    elif role == 'Staff':
        conn = sqlite3.connect('crime_reporting.db')
        cursor = conn.cursor()
        if department == 'Police':
            cursor.execute("SELECT * FROM crime_reports WHERE officer_in_charge IS NULL OR officer_in_charge=?", (session['username'],))
            reports = cursor.fetchall()
            conn.close()
            return render_template('dashboard.html', role=role, department=department, reports=reports)
        
    elif role == 'Admin':
        conn = sqlite3.connect('crime_reporting.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crime_reports")
        all_reports = cursor.fetchall()
        cursor.execute("SELECT * FROM crime_statistics")
        stats = cursor.fetchall()
        conn.close()
        return render_template('dashboard.html', role=role, all_reports=all_reports, stats=stats)
    
    else:
        flash("Access Denied", "error")
        return redirect(url_for('login'))

# Route to Log Out
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    session.pop('department', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Initialize the database on app start
init_db()

if __name__ == '__main__':
    app.run(debug=True)
