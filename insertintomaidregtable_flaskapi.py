from flask import Flask, request, jsonify
import pyodbc

app = Flask(__name)

# Configure your Azure SQL Database connection
server = 'maidsqlppserver.database.windows.net'
database = 'miadsqlpp'
username = 'ysadmin'
password = 'yellowsense@1234'
driver = '{ODBC Driver 18 for SQL Server}'

# Create a database connection
conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')

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
            "EXEC InsertMaidRegistration ?, ?, ?, ?, ?, ?, ?, ?",
            (aadhar_number, name, phone_number, gender, services, locations, timings)
        )
        conn.commit()
        cursor.close()
        return jsonify({"message": "Maid entry added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
