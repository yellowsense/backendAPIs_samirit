from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin  # Import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for your Flask app
app.config['CORS_HEADERS'] = 'Content-Type'

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

# Function to add custom headers to every response
@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://yellowsense.in'  # Replace with your frontend domain
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST'  # You can specify the allowed methods
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'  # You can specify the allowed headers
    return response

@app.route('/society_names', methods=['GET'])
@cross_origin()
def get_society_names():
    try:
        # Execute a SQL query to retrieve society names and IDs
        cursor.execute("SELECT society_id, society_name FROM Society")
        rows = cursor.fetchall()

        # Convert the result into an array of dictionaries with id and name
        society_data = [{"id": row.society_id, "name": row.society_name} for row in rows]

        return jsonify(society_data)  # Return JSON with id and name
    except pyodbc.Error as e:
        return jsonify({"error": str(e)})

@app.route('/insert_maid', methods=['POST'])
@cross_origin()
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
        return jsonify({"error": str(e})

if __name__ == '__main__':
    app.run(debug=True)
