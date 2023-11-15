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
    with pyodbc.connect(connectionString) as conn:
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
        cursor.execute("SELECT ID, Name, Gender, Services, Locations, Timings FROM maidreg")
        rows = cursor.fetchall()
        maidreg_data = []
        for row in rows:
            maid = {
                "ID": row.ID,
                "Name": row.Name,
                "Gender": row.Gender,
                "Services": row.Services.split(','),
                "Locations": row.Locations.split(','),
                "Timings": row.Timings
            }
            maidreg_data.append(maid)
        return maidreg_data
    except pyodbc.Error as e:
        app.logger.error("Error fetching maidreg data: %s", e)
        return []

# Fetch maid data only once when the application starts
service_providers = get_maidreg_data()

def find_matching_service_providers(Locations, Services, date, start_time_str):
    start_time = parse_time_string(start_time_str)
    if start_time is None:
        app.logger.error("Invalid start_time format: %s", start_time_str)
        return {"error": "Invalid start_time format"}
    
    matching_providers = []
    for provider in service_providers:
        # Check if the specified location is in the provider's list of locations
        if isinstance(provider["Locations"], list) and Locations.lower() in [loc.strip().lower() for loc in provider["Locations"]]:
            # Check if the specified service is in the provider's list of services
            if Services.lower() in [serv.strip().lower() for serv in provider["Services"]]:
                # Check if Timings is a valid list
                if ',' in provider["Timings"]:
                    Timings = provider["Timings"].split(',')
                    for timing_range in Timings:
                        start_str, end_str = timing_range.split('-')
                        start = parse_time_string(start_str)
                        end = parse_time_string(end_str)
                        if start is None or end is None:
                            app.logger.error("Invalid timing format in provider %s: %s", provider["ID"], timing_range)
                            continue
                        if start <= start_time < end:
                            matching_providers.append({"ID": provider["ID"], **provider})
                            break  # Break from the inner loop once a match is found for this provider
                else:
                    app.logger.error("Invalid Timings format in provider %s: %s", provider["ID"], provider["Timings"])
    return matching_providers

@app.route('/get_matching_service_providers', methods=['GET', 'POST'])
@cross_origin()
def get_matching_providers():
    if request.method == 'GET':
        Locations = request.args.get('Locations')
        Services = request.args.get('Services')
        date = request.args.get('date')
        start_time = request.args.get('start_time')
    elif request.method == 'POST':
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


if __name__ == '__main__':
    app.run(debug=True)
