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

def get_no_due_data():
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
   
    # Query to get data from the no_due_stat table
    cursor.execute("SELECT * FROM no_due_stat")
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results


# Route to display login form
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/apply_for_documents')
def apply_for_documents():
    usn = session['usn']
     
    return render_template('std_form.html')


@app.route('/management_login', methods=['GET', 'POST'])
def management_login():
    if request.method == 'POST':
        username = request.form['managementEmail']
        password = request.form['managementPassword']

        # Connect to database and verify credentials
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM management_users WHERE username = %s", (username,))
        user = cursor.fetchone()

        # Direct password comparison
        if user and user['password'] == password:
            session['username'] = username  # Save username in session
            return redirect(url_for('managment_dashboard'))
        else:
            flash('Invalid credentials. Please try again.')

        cursor.close()
        conn.close()

    return render_template('management_login.html')



@app.route('/managment_dashboard')
def managment_dashboard():
    return render_template('management_dashboard.html')

@app.route('/no_due_stat')
def no_due_status():
    usn = session.get('usn')  # Get USN from session
    if usn is None:
        return redirect(url_for('student_login'))  # Redirect to login if not logged in

    # Simulated data (replace with your actual data fetching logic)
    # no_due_data = [
    #     {'subject_name': 'Introduction to Computer Science', 'ia_marks1': 18, 'ia_marks2': 17, 'ia_marks3': 19, 'assignment1': 'submitted', 'assignment2': 'submitted'},
    #     {'subject_name': 'Calculus II', 'ia_marks1': 20, 'ia_marks2': 19, 'ia_marks3': 18, 'assignment1': 'submitted', 'assignment2': 'not submitted'},
    #     {'subject_name': 'Physics I', 'ia_marks1': 15, 'ia_marks2': 16, 'ia_marks3': 14, 'assignment1': 'submitted', 'assignment2': 'not submitted'},
    #     # Add more subjects as needed for the specific student
    # ]
    usn=session['usn']  
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
   
    # Query to get data from the no_due_stat table
    cursor.execute("SELECT * FROM no_due_stat where student_usn = %s",(usn,))
    no_due_data = cursor.fetchall()

    cursor.close()
    conn.close()


    # Filter based on the USN (replace this with a database query)
    # Example: query = "SELECT * FROM no_due_status WHERE usn = :usn", params={"usn": usn}

    # Render the template with the filtered data
    return render_template('no_due_stat.html', data=no_due_data,usn=usn)




@app.route('/no_due_update/<subject_name>', methods=['GET', 'POST'])
def no_due_update(subject_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: Fetch the subject_id using subject_name
    cursor.execute("SELECT subject_id FROM subjects WHERE subject_name = %s", (subject_name,))
    subject_result = cursor.fetchone()

    if not subject_result:
        flash(f"Subject {subject_name} not found!", "danger")
        return redirect(url_for('prof_dashboard'))

    subject_id = subject_result['subject_id']

    if request.method == 'POST':
        # Process the submitted form data to update no_due, assignments, and fees
        for key, value in request.form.items():
            if key.startswith('nodue_'):
                # Extract usn from key, e.g., 'nodue_S001'
                usn = key.split('_')[1]

                # Update the database based on form input
                assignment1 = request.form.get(f'assignment1_{usn}', 'not_submitted')
                assignment2 = request.form.get(f'assignment2_{usn}', 'not_submitted')
                fee_due = request.form.get(f'fee_due_{usn}', 'due')

                # Update the nodue table with the new data
                cursor.execute("""
                    UPDATE nodue
                    SET assignment1 = %s, assignment2 = %s, fee_due = %s
                    WHERE usn = %s AND subject_id = %s
                """, (assignment1, assignment2, fee_due, usn, subject_id))

        conn.commit()
        flash("No Due information updated successfully!", "success")
        return redirect(url_for('no_due_update', subject_name=subject_name))

    # Fetch students and their no-due status for this subject
    cursor.execute("""
        SELECT s.usn, s.name, ia.ia_marks1, ia.ia_marks2, ia.ia_marks3, 
               n.assignment1, n.assignment2, n.fee_due
        FROM students s
        LEFT JOIN ia_marks ia ON s.usn = ia.usn AND ia.subject_id = %s
        LEFT JOIN nodue n ON s.usn = n.usn AND n.subject_id = %s
    """, (subject_id, subject_id))

    students = cursor.fetchall()
    conn.close()

    return render_template('no_due_update.html', subject_name=subject_name, students=students)



@app.route('/prof_logout', methods=['POST'])
def prof_logout():
    session.clear()  # Clear the user session
    return redirect(url_for('prof_login'))  # Redirect to the login page

@app.route('/std_logout', methods=['POST'])
def std_logout():
    session.clear()  # Clear the user session
    return redirect(url_for('student_login'))  # Redirect to the login page




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
            session['usn'] = usn
            return redirect(url_for('student_dashboard'))  # Redirect to dashboard or home page after login
        else:
            # Failed login
            flash("Invalid USN or password", 'danger')

    return render_template('std_login.html')

@app.route('/prof_login', methods=['GET', 'POST'])
def prof_login():
    if request.method == 'POST':
        email = request.form['facultyEmail']
        password = request.form['facultyPassword']
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
    conn.close()
    
    # Pass the subjects to the template
    return render_template('prof_dashboard.html', name=name, designation=designation, department=department, subjects=subjects)


@app.route('/subject/<subject_name>')
def subject_page(subject_name):
    # Logic to render the subject page
    return render_template('subject.html', subject_name=subject_name)

@app.route('/subject/<subject_name>/update_attendance', methods=['GET', 'POST'])
def update_attendance(subject_name):
    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Use dictionary=True to fetch rows as dictionaries

    # Step 1: Fetch the subject_id using subject_name
    cursor.execute("SELECT subject_id FROM subjects WHERE subject_name = %s", (subject_name,))
    result = cursor.fetchone()

    if not result:
        # If the subject is not found, show an error or handle accordingly
        
        return redirect(url_for('prof_dashboard'))

    # Safely access the subject_id from the result
    subject_id = result.get('subject_id')

    if request.method == 'POST':
        # Process the form submission for attendance update
        usn = request.form['usn']
        attendance = request.form['attendance']

        # Update the attendance in the database
        cursor.execute(
            "UPDATE attendance SET attendance = %s WHERE usn = %s AND subject_id = %s",
            (attendance, usn, subject_id)
        )
        conn.commit()  # Commit the transaction

        
        return redirect(url_for('update_attendance', subject_name=subject_name))
    
    # Fetch students and their attendance for this subject
    cursor.execute("SELECT s.usn,s.name, a.attendance FROM students s JOIN attendance a on s.usn = a.usn where a.subject_id = %s", (subject_id,))
    
    students = cursor.fetchall()

    conn.close()  # Close the database connection

    # Render the update attendance page
    return render_template('update_attendance.html', subject_name=subject_name, students=students)



@app.route('/subject/<subject_name>/update_ia_marks', methods=['GET', 'POST'])
def update_ia_marks(subject_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Use dictionary=True to fetch rows as dictionaries

    # Step 1: Fetch the subject_id using subject_name
    cursor.execute("SELECT subject_id FROM subjects WHERE subject_name = %s", (subject_name,))
    result = cursor.fetchone()

    if not result:
        flash(f"Subject {subject_name} not found!", "danger")
        return redirect(url_for('prof_dashboard'))

    # Store subject_id in session
    session['subject_id'] = result['subject_id']

    # If the request method is POST, update the IA marks
    if request.method == 'POST':
        usn = request.form['usn']
        ia_marks1 = request.form['ia_marks1']
        ia_marks2 = request.form['ia_marks2']
        ia_marks3 = request.form['ia_marks3']
        
        # Retrieve subject_id from session
        subject_id = session.get('subject_id')

        # Update the IA marks in the database
        cursor.execute("""
            UPDATE ia_marks 
            SET ia_marks1 = %s, ia_marks2 = %s, ia_marks3 = %s 
            WHERE usn = %s AND subject_id = %s
        """, (ia_marks1, ia_marks2, ia_marks3, usn, subject_id))
        conn.commit()  # Commit the transaction

        
        return redirect(url_for('update_ia_marks', subject_name=subject_name))

    # Fetch students and their IA marks using JOIN
    subject_id = session.get('subject_id')  # Retrieve subject_id from session
    cursor.execute("""
        SELECT students.usn, students.name, ia_marks.ia_marks1, ia_marks.ia_marks2, ia_marks.ia_marks3 
        FROM students
        JOIN ia_marks ON students.usn = ia_marks.usn
        WHERE ia_marks.subject_id = %s
    """, (subject_id,))
    
    students = cursor.fetchall()

    conn.close()  # Close the database connection

    # Render the update IA marks page
    return render_template('update_ia_marks.html', subject_name=subject_name, students=students)

@app.route('/subject_materials/<subject_name>')
def subject_materials(subject_name):
    # Retrieve the subject's materials (PDFs) from the database or filesystem
    # For demonstration purposes, we'll use a placeholder list of PDFs.
    # You should fetch this data based on the subject_name from your database or filesystem.
    pdfs = [
        f"{subject_name}_material1.pdf",
        f"{subject_name}_material2.pdf",
        f"{subject_name}_material3.pdf"
    ]
    
    return render_template('subject_materials.html', subject_name=subject_name, pdfs=pdfs)



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

    return redirect(url_for('prof_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
