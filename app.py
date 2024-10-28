from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename  # Add this line

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/citizen/register', methods=['GET', 'POST'])
def citizen_register():
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO citizens (name, mobile, password) VALUES (?, ?, ?)', 
                           (name, mobile, password))
            conn.commit()
            return redirect(url_for('citizen_login'))
        except sqlite3.IntegrityError:
            return "Mobile number already registered!"
        finally:
            conn.close()
    return render_template('citizen_register.html')
@app.route('/citizen/submit_complaint', methods=['POST'])
def submit_complaint():
    mobile = request.form['mobile']
    location = request.form['location']
    crime_type = request.form['crime_type']
    description = request.form['description']
    department = request.form['department']
    image = request.files['image']

    # Save image if uploaded
    image_filename = ''
    if image:
        image_filename = image.filename
        image.save(f'static/uploads/{image_filename}')

    # Connect to the database
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Insert the complaint into the database
    c.execute('''
        INSERT INTO complaints (id, description, status, department, image)
        VALUES (
            (SELECT id FROM citizens WHERE mobile = ?),
            ?, 'Pending', ?, ?
        )
    ''', (mobile, description, department, image_filename))

    conn.commit()
    conn.close()

    return redirect(url_for('citizen_dashboard'))

@app.route('/citizen/login', methods=['GET', 'POST'])
def citizen_login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM citizens WHERE mobile = ? AND password = ?', (mobile, password))
        citizen = cursor.fetchone()
        conn.close()
        
        if citizen:
            session['id'] = citizen['id']
            return redirect(url_for('citizen_dashboard'))
        else:
            return "Invalid mobile or password!"
    return render_template('citizen_login.html')

@app.route('/citizen/dashboard')
def citizen_dashboard():
    if 'id' not in session:
        return redirect(url_for('citizen_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM citizens WHERE id = ?', (session['id'],))
    citizen = cursor.fetchone()
    
    cursor.execute('SELECT * FROM complaints WHERE id = ?', (citizen['id'],))
    complaints = cursor.fetchall()
    conn.close()

    return render_template('citizen_dashboard.html', citizen=citizen, complaints=complaints)

@app.route('/citizen/complaint', methods=['GET', 'POST'])
def citizen_complaint():
    if 'id' not in session:
        return redirect(url_for('citizen_login'))

    if request.method == 'POST':
        mobile = request.form['mobile']
        location = request.form['location']
        crime_type = request.form['crime_type']
        station = request.form['station']
        description = request.form['description']
        image = request.files['image']
        
        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        else:
            image_filename = None

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO complaints (id, mobile, location, crime_type, station, description, status, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (session['id'], mobile, location, crime_type, station, description, 'Pending', image_filename))
        conn.commit()
        conn.close()
        
        return redirect(url_for('citizen_dashboard'))
    return render_template('citizen_complaint.html')

@app.route('/citizen/logout')
def citizen_logout():
    session.pop('id', None)
    return redirect(url_for('home'))

@app.route('/police/register', methods=['GET', 'POST'])
def police_register():
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        password = request.form['password']
        department=request.form['department']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO police (name, mobile, password,department) VALUES (?, ?, ?,?)', 
                           (name, mobile, password,department))
            conn.commit()
            return redirect(url_for('police_login'))
        except sqlite3.IntegrityError:
            return "Mobile number already registered!"
        finally:
            conn.close()
    return render_template('police_register.html')


@app.route('/police/login', methods=['GET', 'POST'])
def police_login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM police WHERE mobile = ? AND password = ?', (mobile, password))
        police = cursor.fetchone()
        conn.close()

        if police:
            session['police_id'] = police['id']
            return redirect(url_for('police_dashboard'))
        else:
            return "Invalid mobile or password!"
    return render_template('police_login.html')

# Route for the police dashboard
@app.route('/police/dashboard')
def police_dashboard():
    if 'police_id' not in session:
        return redirect(url_for('police_login'))

    department = session.get('department')  # Get department from session
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve complaints for the specific department
    cursor.execute('SELECT * FROM complaints WHERE department = ?', (department,))
    complaints = cursor.fetchall()
    
    conn.close()
    return render_template('police_dashboard.html', complaints=complaints)

@app.route('/police/update/<int:complaint_id>', methods=['POST'])
def police_update(complaint_id):
    if 'police_id' not in session:
        return redirect(url_for('police_login'))

    status = request.form['status']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE complaints SET status = ? WHERE id = ?', (status, complaint_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('police_dashboard'))

@app.route('/police/logout')
def police_logout():
    # Remove police session data
    session.pop('police_id', None)
    session.pop('police_mobile', None)
    return redirect(url_for('home'))

@app.route('/complaint/status/<int:complaint_id>')
def complaint_status(complaint_id):
    if 'id' not in session:
        return redirect(url_for('citizen_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,))
    complaint = cursor.fetchone()
    conn.close()

    return render_template('status.html', complaint=complaint)

if __name__ == '__main__':
    app.run(debug=True)
