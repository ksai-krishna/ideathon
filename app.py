from flask import Flask, render_template, request, redirect, url_for, flash,session
import mysql.connector
from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management (e.g., flash messages)

# Function to connect to the database
def get_db_connection():
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['pass'],
        database="camb"
    )
    return conn

# Route to display login form
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        usn = request.form['username']
        password = request.form['password']

        # Check if the user exists in the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE usn = %s AND password = %s", (usn, password))
        user = cursor.fetchone()

        conn.close()

        if user:
            # Successful login
            flash(f"Welcome, {user['name']}!", 'success')
            return redirect(url_for('student_dashboard'))  # Redirect to dashboard or home page after login
        else:
            # Failed login
            flash("Invalid USN or password", 'danger')

    return render_template('std_login.html')

@app.route('/prof_login', methods=['GET', 'POST'])
def prof_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Check if the user exists in the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM teachers WHERE email_id = %s AND password = %s", (email, password))
        teacher = cursor.fetchone()
        conn.close()
        if teacher:
            session['name'] = teacher['name']
            session['email_id'] = teacher['email_id']
            session['designation'] = teacher['designation']
            session['department'] = teacher['department']

            # Successful login
            
            return redirect(url_for('prof_dashboard'))  # Redirect to dashboard or home page after login
        else:
            # Failed login
            flash("Invalid email or password", 'danger')

    return render_template('prof_login.html')

# Dummy dashboard route (only accessible after login)
@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/prof_dashboard')
def prof_dashboard():
    name = session['name']
    email_id = session['email_id']  # Assuming the email_id is stored in session
    designation = session['designation']
    department = session['department']
    
    # Fetch the subjects handled by the teacher
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Assuming there's a `subjects` table and the teacher's subjects are associated with their email or id
    cursor.execute("SELECT subject_name FROM subject_handled WHERE teacher_email = %s", (email_id,))
    subjects = cursor.fetchall()  # Fetch all subjects handled by the teacher
    for sub in subjects:
        print(sub)
        print("hi")
    conn.close()
    
    # Pass the subjects to the template
    return render_template('prof_dashboard.html', name=name, designation=designation, department=department, subjects=subjects)


@app.route('/subject/<subject_name>', methods=['GET', 'POST'])
def subject(subject_name):
    if request.method == 'POST':
        # Handle form submission for updating IA marks (if applicable)
        pass

    # Fetch student details and IA marks for the specified subject
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.usn, s.name, ia.ia_marks1, ia.ia_marks2, ia.ia_marks3
        FROM students s
        JOIN ia_marks ia ON s.usn = ia.usn
        JOIN subjects sub ON ia.subject_id = sub.subject_id
        WHERE sub.subject_name = %s
    """, (subject_name,))
    students = cursor.fetchall()
    conn.close()
    
    return render_template('subject.html', subject_name=subject_name, students=students)




@app.route('/submit_nodue', methods=['POST'])
def submit_nodue():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Loop through form data to check which students and subjects have 'No Due'
    for key, value in request.form.items():
        if key.startswith('nodue_') and value == 'on':
            # Extract USN and subject_id from the checkbox name
            parts = key.split('_')
            usn = parts[1]
            subject_id = parts[2]

            # Update the nodue table
            cursor.execute(""" 
                INSERT INTO nodue (teacher_email, subject_id, usn, nodue) 
                VALUES (%s, %s, %s, TRUE)
                ON DUPLICATE KEY UPDATE nodue = TRUE
            """, (request.form['teacher_email'], subject_id, usn))

    conn.commit()
    conn.close()

    flash('No Due status updated successfully!', 'success')
    return redirect(url_for('prof_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
