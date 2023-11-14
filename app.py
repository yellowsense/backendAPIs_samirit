from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import pyodbc
from datetime import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

# Database connection setup
SERVER = 'maidsqlppserver.database.windows.net'
DATABASE = 'miadsqlpp'
USERNAME = 'ysadmin'
PASSWORD = 'yellowsense@1234'
connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'

try:
    conn = pyodbc.connect(connectionString)
    app.logger.info("Connected to the database.")
    cursor = conn.cursor()
except pyodbc.Error as e:
    app.logger.error("Error connecting to the database: %s", e)
    raise

# Function to add custom headers to every response
@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://yellowsense.in'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

def parse_time_string(time_str):
    try:
        time_parts = time_str.split(':')
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        return time(hours, minutes)
    except ValueError:
        return None

def get_maidreg_data():
    try:
        cursor.execute("SELECT Name, Gender, Services, Locations, Timings FROM maidreg")
        rows = cursor.fetchall()

        # Convert the result into a list of dictionaries
        maidreg_data = []
        for row in rows:
            maid = {
                "Name": row.Name,
                "Gender": row.Gender,
                "Services": row.Services.split(','),
                "Locations": row.Locations.split(','),
                "Timings": row.Timings
            }
            maidreg_data.append(maid)

        return maidreg_data
    except pyodbc.Error as e:
        return []

service_providers = get_maidreg_data()

def find_matching_service_providers(Locations, Services, date, start_time_str):
    # Parse the start_time from the input
    start_time = parse_time_string(start_time_str)

    if start_time is None:
        return {"error": "Invalid start_time format"}

    matching_providers = []

    for provider in service_providers:
        if any(service in Services for service in provider["Services"]):
            if any(location in Locations for location in provider["Locations"]):
                # Assume that providers are available on all dates
                # Parse the timings string into time ranges
                Timings = provider["Timings"].split(',')
                for timing_range in Timings:
                    start_str, end_str = timing_range.split('-')
                    start = parse_time_string(start_str)
                    end = parse_time_string(end_str)

                    if start is None or end is None:
                        return {"error": "Invalid timing format"}

                    # Check if the start_time falls within the timing range
                    if start <= start_time < end:
                        matching_providers.append(provider)
                        break  # No need to check other timing ranges for this provider

    return matching_providers

@app.route('/get_matching_service_providers', methods=['GET', 'POST'])
@cross_origin()
def get_matching_providers():
    if request.method == 'GET':
        # Extract parameters from the URL for GET requests
        Locations = request.args.get('Locations')
        Services = request.args.get('Services')
        date = request.args.get('date')
        start_time = request.args.get('start_time')
    elif request.method == 'POST':
        # Extract parameters from the JSON body for POST requests
        data = request.json
        Locations = data.get('Locations')
        Services = data.get('Services')
        date = data.get('date')
        start_time = data.get('start_time')
    else:
        return jsonify({"error": "Unsupported method"})

    if not Locations or not Services or not date or not start_time:
        return jsonify({"error": "Missing parameters"})

    matching_providers = find_matching_service_providers(Locations, Services, date, start_time)

    if matching_providers:
        return jsonify({"providers": matching_providers})
    else:
        return jsonify({"providers": "No matching service providers found"})

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
        # Extract parameters from the JSON body for POST requests
        data = request.json
        aadhar_number = data.get('AadharNumber')
        name = data.get('Name')
        phone_number = data.get('PhoneNumber')
        gender = data.get('Gender')
        services = data.get('Services')
        locations = data.get('Locations')
        timings = data.get('Timings')

        # Execute the stored procedure
        cursor = conn.cursor()
        cursor.execute(
            "EXEC InsertMaidRegistration "
            "@AadharNumber = ?, "
            "@Name = ?, "
            "@PhoneNumber = ?, "
            "@Gender = ?, "
            "@Services = ?, "
            "@Locations = ?, "
            "@Timings = ?",
            (aadhar_number, name, phone_number, gender, services, locations, timings)
        )
        conn.commit()
        cursor.close()

        # Return a success message
        return jsonify({"message": "Maid entry added successfully"})
    except Exception as e:
        # Log the error and return an error message in case of an exception
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500
        
@app.route('/get_all_maid_details', methods=['GET'])
@cross_origin()
def get_all_maid_details():
    try:
        cursor.execute("SELECT * FROM maidreg")
        rows = cursor.fetchall()

        maid_details_list = []
        for row in rows:
            maid_details = {
                "ID": row.ID,
                "AadharNumber": row.AadharNumber,
                "Name": row.Name,
                "PhoneNumber": row.PhoneNumber,
                "Gender": row.Gender,
                "Services": row.Services.split(','),
                "Locations": row.Locations.split(','),
                "Timings": row.Timings
            }
            maid_details_list.append(maid_details)

        return jsonify({"maid_details": maid_details_list})
    except pyodbc.Error as e:
        return jsonify({"error": str(e)})

@app.route('/get_maid_details/<int:maid_id>', methods=['GET'])
@cross_origin()
def get_maid_details(maid_id):
    try:
        cursor.execute("SELECT * FROM maidreg WHERE ID=?", (maid_id,))
        row = cursor.fetchone()

        if row:
            maid_details = {
                "ID": row.ID,
                "AadharNumber": row.AadharNumber,
                "Name": row.Name,
                "PhoneNumber": row.PhoneNumber,
                "Gender": row.Gender,
                "Services": row.Services.split(','),
                "Locations": row.Locations.split(','),
                "Timings": row.Timings
            }
            return jsonify(maid_details)
        else:
            return jsonify({"error": "Maid not found"})
    except pyodbc.Error as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
