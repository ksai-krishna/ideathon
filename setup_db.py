import mysql.connector
from config import DB_CONFIG


# Connect to the MySQL database (change the user, password, and database name as per your setup)
conn = mysql.connector.connect(
    host=DB_CONFIG['host'],   # Localhost (your MySQL server IP)
    user=DB_CONFIG['user'],  # MySQL username
    password=DB_CONFIG['pass'],  # MySQL password
    database="people"  # Database name
)

c = conn.cursor()

# Create table if it doesn't exist
q = ''' CREATE TABLE IF NOT EXISTS people (
             id INT AUTO_INCREMENT PRIMARY KEY,
             name VARCHAR(255) NOT NULL)'''
c.execute(q)

# Insert some sample data
c.execute("INSERT INTO people (name) VALUES ('John Doe')")
c.execute("INSERT INTO people (name) VALUES ('Jane Smith')")
c.execute("INSERT INTO people (name) VALUES ('Alice Johnson')")

# Fetch and display all records from the people table
c.execute("SELECT * FROM people")
rows = c.fetchall()

# Print the results
for row in rows:
    print(row)

# Commit the transaction and close the connection
conn.commit()
conn.close()
