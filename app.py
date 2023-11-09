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
    cursor = conn.cursor()
except pyodbc.Error as e:
    print("Error connecting to the database:", e)

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
    start_time = parse_time_string(start_time_str)

    if start_time is None:
        return {"error": "Invalid start_time format"}

    matching_providers = []

    for provider in service_providers:
        if any(service in Services for service in provider["Services"]):
            if any(location in Locations for location in provider["Locations"]):
                Timings = provider["Timings"].split(',')
                for timing_range in Timings:
                    start_str, end_str = timing_range.split('-')
                    start = parse_time_string(start_str)
                    end = parse_time_string(end_str)

                    if start is None or end is None:
                        return {"error": "Invalid timing format"}

                    if start <= start_time < end:
                        matching_providers.append(provider)
                        break

    return matching_providers

@app.route('/society_names', methods=['GET'])
@cross_origin()
def get_society_names():
    try:
        cursor.execute("SELECT society_id, society_name FROM Society")
        rows = cursor.fetchall()
        society_data = [{"id": row.society_id, "name": row.society_name} for row in rows]
        return jsonify(society_data)
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
        return jsonify({"error": str(e)})

@app.route('/get_matching_service_providers', methods=['GET', 'POST'])
@cross_origin()
def get_matching_providers():
    data = request.get_json()
    Locations = data.get('Locations')
    Services = data.get('Services')
    date = data.get('date')
    start_time = data.get('start_time')

    if not Locations or not Services or not date or not start_time:
        return jsonify({"error": "Missing parameters"})

    matching_providers = find_matching_service_providers(Locations, Services, date, start_time)

    if matching_providers:
        return jsonify({"providers": matching_providers})
    else:
        return jsonify({"providers": "No matching service providers found"})

if __name__ == '__main__':
    app.run(debug=True)
