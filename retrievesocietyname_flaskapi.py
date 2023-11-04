from flask import Flask, request, jsonify
import pyodbc

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change to a strong secret key

# Database connection setup
SERVER = 'maidsqlppserver.database.windows.net'
DATABASE = 'miadsqlpp'
USERNAME = 'ysadmin'
PASSWORD = 'yellowsense@1234'
connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'

try:
    conn = pyodbc.connect(connectionString)
    cursor = conn.cursor()
except pyodbc.Error as e:
    print("Error connecting to the database:", e)

@app.route('/society_names', methods=['GET'])
def get_society_names():
    try:
        # Execute a SQL query to retrieve society names
        cursor.execute("SELECT society_name FROM Society")
        rows = cursor.fetchall()

        # Convert the result into a list of society names
        society_names = [row.society_name for row in rows]

        return jsonify({"society_names": society_names})
    except pyodbc.Error as e:
        return jsonify({"error": str(e})

if __name__ == '__main__':
    app.run(debug=True)
