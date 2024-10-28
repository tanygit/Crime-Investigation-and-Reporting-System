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
            session['citizen_id'] = citizen['id']
            return redirect(url_for('citizen_dashboard'))
        else:
            return "Invalid mobile or password!"
    return render_template('citizen_login.html')

@app.route('/citizen/dashboard')
def citizen_dashboard():
    if 'citizen_id' not in session:
        return redirect(url_for('citizen_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM citizens WHERE id = ?', (session['citizen_id'],))
    citizen = cursor.fetchone()
    
    cursor.execute('SELECT * FROM complaints WHERE citizen_id = ?', (citizen['id'],))
    complaints = cursor.fetchall()
    conn.close()

    return render_template('citizen_dashboard.html', citizen=citizen, complaints=complaints)

@app.route('/citizen/complaint', methods=['GET', 'POST'])
def citizen_complaint():
    if 'citizen_id' not in session:
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
        cursor.execute('INSERT INTO complaints (citizen_id, mobile, location, crime_type, station, description, status, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (session['citizen_id'], mobile, location, crime_type, station, description, 'Pending', image_filename))
        conn.commit()
        conn.close()
        
        return redirect(url_for('citizen_dashboard'))
    return render_template('citizen_complaint.html')

@app.route('/citizen/logout')
def citizen_logout():
    session.pop('citizen_id', None)
    return redirect(url_for('home'))

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

@app.route('/police/dashboard')
def police_dashboard():
    if 'police_id' not in session:
        return redirect(url_for('police_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM complaints')
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

@app.route('/complaint/status/<int:complaint_id>')
def complaint_status(complaint_id):
    if 'citizen_id' not in session:
        return redirect(url_for('citizen_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,))
    complaint = cursor.fetchone()
    conn.close()

    return render_template('status.html', complaint=complaint)

if __name__ == '__main__':
    app.run(debug=True)
