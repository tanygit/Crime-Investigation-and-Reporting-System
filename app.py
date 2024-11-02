from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename  # Add this line

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DEBUG'] = True  # Enable debug mode


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
        profile_image = request.files['profile_image']  # Get the uploaded image

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Save the profile image if uploaded
            image_filename = secure_filename(profile_image.filename)
            profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            cursor.execute('INSERT INTO citizens (name, mobile, password, profile_image) VALUES (?, ?, ?, ?)', 
                           (name, mobile, password, image_filename))
            conn.commit()
            return redirect(url_for('citizen_login'))
        except sqlite3.IntegrityError:
            return "Mobile number already registered!"
        finally:
            conn.close()
    return render_template('citizen_register.html')

@app.route('/citizen/submit_complaint', methods=['POST'])
def submit_complaint():
    if 'id' not in session:  # Check if the citizen is logged in
        return redirect(url_for('citizen_login'))

    citizen_id = session['id']  # Retrieve citizen ID from session
    location = request.form['location']
    crime_type = request.form['crime_type']
    description = request.form['description']
    department = request.form['department']
    image = request.files['image']

    # Save image if uploaded
    image_filename = ''
    if image:
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert the complaint into the database, including citizen_id
    cursor.execute('''
        INSERT INTO complaints (citizen_id, description, status, department, image)
        VALUES (?, ?, 'Pending', ?, ?)
    ''', (citizen_id, description, department, image_filename))

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
    
    cursor.execute('SELECT * FROM complaints WHERE citizen_id = ?', (citizen['id'],))
    complaints = cursor.fetchall()
    conn.close()

    return render_template('citizen_dashboard.html', citizen=citizen, complaints=complaints)

@app.route('/citizen/complaint', methods=['GET', 'POST'])
def citizen_complaint():
    if 'id' not in session:
        return redirect(url_for('citizen_login'))

    if request.method == 'POST':
        citizen_id = session['id']  # Retrieve citizen ID from session
        location = request.form['location']
        crime_type = request.form['crime_type']
        station = request.form['station']
        description = request.form['description']
        image = request.files['image']
        
        image_filename = None
        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO complaints (citizen_id, location, crime_type, station, description, status, image)
            VALUES (?, ?, ?, ?, ?, 'Pending', ?)
        ''', (citizen_id, location, crime_type, station, description, image_filename))
        
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
        department = request.form['department']

        # Handle profile image upload
        profile_image = request.files['profile_image']
        if profile_image:
            image_filename = secure_filename(profile_image.filename)
            profile_image.save(os.path.join('static/uploads', image_filename))

        # Save the police officer to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO police (name, mobile, password, department, profile_image)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, mobile, password, department, image_filename))
        conn.commit()
        conn.close()

        return redirect(url_for('police_login'))

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
            session['department'] = police['department']
            return redirect(url_for('police_dashboard'))
        else:
            return "Invalid mobile or password!"
    return render_template('police_login.html')

@app.route('/police/dashboard', methods=['GET'])
def police_dashboard():
    if 'police_id' not in session:
        return redirect(url_for('police_login'))

    police_id = session['police_id']
    department = session['department']
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve police information including profile image
    cursor.execute('SELECT * FROM police WHERE id = ?', (police_id,))
    police = cursor.fetchone()

    # Retrieve complaints for the specific department
    cursor.execute('SELECT * FROM complaints WHERE department = ?', (department,))
    complaints = cursor.fetchall()

    conn.close()

    return render_template('police_dashboard.html', police=police, complaints=complaints)



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

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Insert new admin into the database
        cursor.execute('INSERT INTO admin (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('admin_login'))

    return render_template('admin_register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')  # Use get to avoid KeyError
        password = request.form.get('password')

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            # Check admin credentials
            cursor.execute('SELECT * FROM admin WHERE username = ? AND password = ?', (username, password))
            admin = cursor.fetchone()
        except Exception as e:
            return f"An error occurred: {e}"
        finally:
            conn.close()

        if admin:
            session['admin_id'] = admin[0]  # Store admin id in session
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid username or password"

    return render_template('admin_login.html')



@app.route('/admin/dashboard')
def admin_dashboard():
    # Get admin's name
    admin_id = session.get('admin_id')
    admin_name = ''
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch admin name based on admin_id
    cursor.execute('SELECT username FROM admin WHERE id = ?', (admin_id,))
    admin_data = cursor.fetchone()
    if admin_data:
        admin_name = admin_data[0]

    # Fetch case counts by department
    cursor.execute('''
        SELECT department, COUNT(*) as count
        FROM complaints
        GROUP BY department
    ''')
    case_counts = cursor.fetchall()

    # Fetch status counts
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM complaints
        GROUP BY status
    ''')
    status_counts = cursor.fetchall()

    conn.close()

    # Pass admin_name, case_counts, and status_counts to the template
    return render_template('admin_dashboard.html', 
                           case_counts=case_counts, 
                           status_counts=status_counts, 
                           admin_name=admin_name)


# Route to delete a complaint
@app.route('/complaint/delete/<int:complaint_id>', methods=['GET','POST'])
def delete_complaint(complaint_id):
    if 'id' not in session and 'police_id' not in session:
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM complaints WHERE id = ?', (complaint_id,))
    conn.commit()
    conn.close()
    if 'id' in session:
        return redirect(url_for('citizen_dashboard'))
    elif 'police_id' in session:
        return redirect(url_for('police_dashboard'))
    
@app.route('/citizen/update_complaint/<int:complaint_id>', methods=['GET', 'POST'])
def citizen_update_complaint(complaint_id):
    if 'id' not in session:
        return redirect(url_for('citizen_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch the complaint to update
    cursor.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,))
    complaint = cursor.fetchone()

    if request.method == 'POST':
        description = request.form['description']
        
        cursor.execute('''
            UPDATE complaints SET description = ?
            WHERE id = ?
        ''', (description,complaint_id))

        conn.commit()
        conn.close()
        return redirect(url_for('citizen_dashboard'))

    conn.close()
    return render_template('citizen_update_complaint.html', complaint=complaint)

def get_citizen(citizen_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM citizens WHERE id = ?', (citizen_id,))
    citizen = cursor.fetchone()
    conn.close()
    return citizen

def update_citizen(citizen_id, name=None, mobile=None, profile_image=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update citizen's information
    if profile_image:
        cursor.execute('''
            UPDATE citizens SET name = ?, mobile = ?, profile_image = ?
            WHERE id = ?
        ''', (name, mobile, profile_image, citizen_id))
    else:
        cursor.execute('''
            UPDATE citizens SET name = ?, mobile = ?
            WHERE id = ?
        ''', (name, mobile, citizen_id))
    
    conn.commit()
    conn.close()

def delete_citizen(citizen_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM citizens WHERE id = ?', (citizen_id,))
    conn.commit()
    conn.close()


@app.route('/citizen/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'id' not in session:
        return redirect(url_for('citizen_login'))

    citizen_id = session['id']  # Retrieve citizen ID from session
    citizen = get_citizen(citizen_id)  # Fetch the citizen's current data

    if request.method == 'POST':
        new_name = request.form.get('name')
        new_mobile = request.form.get('mobile')

        # Handle profile image upload
        profile_image_filename = citizen['profile_image']  # Default to current image
        if 'profile_image' in request.files:
            profile_image = request.files['profile_image']
            if profile_image.filename:  # Only save if a new image is provided
                profile_image_filename = secure_filename(profile_image.filename)
                profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_image_filename))
        
        # Update the citizen in the database
        update_citizen(citizen_id, name=new_name, mobile=new_mobile, profile_image=profile_image_filename)
        return redirect(url_for('citizen_dashboard'))

    return render_template('update_profile.html', citizen=citizen)

@app.route('/citizen/delete_profile', methods=['GET','POST'])
def delete_profile():
    if 'id' not in session:
        return redirect(url_for('citizen_login'))

    citizen_id = session['id']
    delete_citizen(citizen_id)  # Call the function to delete the citizen's data from the database
    session.pop('id', None)  # Clear the session
    return redirect(url_for('home'))  # Redirect to the homepage or login page after deletion

@app.route('/police/update_profile', methods=['GET', 'POST'])
def police_update_profile():
    if 'police_id' not in session:
        return redirect(url_for('police_login'))

    police_id = session['police_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the police officer's current data
    cursor.execute('SELECT * FROM police WHERE id = ?', (police_id,))
    police = cursor.fetchone()

    if request.method == 'POST':
        new_name = request.form.get('name')
        new_mobile = request.form.get('mobile')
        new_department = request.form.get('department')

        # Handle profile image upload
        profile_image_filename = police['profile_image']  # Default to current image
        if 'profile_image' in request.files:
            profile_image = request.files['profile_image']
            if profile_image.filename:  # Only save if a new image is provided
                profile_image_filename = secure_filename(profile_image.filename)
                profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_image_filename))

        # Update the police officer in the database
        cursor.execute('''
            UPDATE police SET name = ?, mobile = ?, department = ?, profile_image = ?
            WHERE id = ?
        ''', (new_name, new_mobile, new_department, profile_image_filename, police_id))

        conn.commit()
        conn.close()
        return redirect(url_for('police_dashboard'))

    conn.close()
    return render_template('police_update_profile.html', police=police)


@app.route('/police/delete_profile', methods=['POST'])
def police_delete_profile():
    if 'police_id' not in session:
        return redirect(url_for('police_login'))

    police_id = session['police_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete the police officer from the database
    cursor.execute('DELETE FROM police WHERE id = ?', (police_id,))
    conn.commit()
    conn.close()

    session.pop('police_id', None)  # Clear the session
    return redirect(url_for('home'))  # Redirect to the homepage after deletion


@app.route('/admin/logout')
def admin_logout():
    # Clear the session
    session.pop('admin_id', None)  # Adjust based on how you store admin session data
    return redirect(url_for('home'))  # Redirect to admin login page or any other page

if __name__ == '__main__':
    app.run(debug=True)
