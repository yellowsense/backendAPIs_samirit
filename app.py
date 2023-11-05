from flask import Flask, request, jsonify
import pyodbc

app = Flask(__name__)

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

        # Convert the result into an array of society names
        society_names = [row.society_name for row in rows]

        return jsonify(society_names)  # Return an array directly in JSON
    except pyodbc.Error as e:
        return jsonify({"error": str(e)})

@app.route('/insert_maid', methods=['POST'])
def insert_maid():
    try:
        data = request.get_json()
        aadhar_number = data.get('aadhar_number')
        name = data.get('name')
        phone_number = data.get('phone_number')
        gender = data.get('gender')
        services = data.get('services')
        locations = data.get('locations')
        timings = data.get('timings')

        cursor = conn.cursor()
        cursor.execute(
            "EXEC InsertMaidRegistration ?, ?, ?, ?, ?, ?, ?",
            (aadhar_number, name, phone_number, gender, services, locations, timings)
        )
        conn.commit()
        cursor.close()
        return jsonify({"message": "Maid entry added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
