from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import pyodbc
from datetime import time
from dateutil import parser
import uuid

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
                "Services": [serv.strip().strip("'").lower() for serv in row.Services.split(',')],
                "Locations": row.Locations.split(','),
                "Timings": [timing.strip().strip("'") for timing in row.Timings.split(',')]
            }
            return jsonify(maid_details)
        else:
            return jsonify({"error": "Maid not found"})
    except pyodbc.Error as e:
        return jsonify({"error": str(e)})


# Function to add custom headers to every response
def parse_time_string(time_str):
    try:
        start_str, end_str = time_str.split('-')
        start_time = parser.parse(start_str).time()
        end_time = parser.parse(end_str).time()
        return start_time, end_time
    except ValueError:
        return None, None

def get_maidreg_data():
    try:
        cursor.execute("SELECT ID, Name, Gender, Services, Locations, Timings FROM maidreg")
        rows = cursor.fetchall()
        maidreg_data = []
        for row in rows:
            services = [service.strip("' ") for service in row.Services.split(',')] if row.Services else []
            locations = [location.strip("' ") for location in row.Locations.split(',')] if row.Locations else []
            timings = [timing.strip("' ") for timing in row.Timings.split(',')] if row.Timings else []
            maid = {
                "ID": row.ID,
                "Name": row.Name,
                "Gender": row.Gender,
                "Services": services,
                "Locations": locations,
                "Timings": timings
            }

            maidreg_data.append(maid)
        return maidreg_data
    except pyodbc.Error as e:
        app.logger.error("Error fetching maidreg data: %s", e)
        return []

# Fetch maid data only once when the application starts
service_providers = get_maidreg_data()

def find_matching_service_providers(Locations, Services, date, start_time_str):
    start_time = parser.parse(f'1900-01-01 {start_time_str}').time()
    if start_time is None:
        app.logger.error("Invalid start_time format: %s", start_time_str)
        return {"error": "Invalid start_time format"}

    matching_providers = []
    for provider in service_providers:
        # Check if the specified location is in the provider's list of locations
        if isinstance(provider["Locations"], list) and provider["Locations"] is not None:
            # Split Locations into a list and perform case-insensitive and whitespace-insensitive comparison
            specified_locations = [loc.strip("' ").lower() for loc in Locations.split(',')]
            provider_locations = [loc.strip("' ").lower() for loc in provider["Locations"]]

            if any(location in provider_locations for location in specified_locations):
                # Check if the specified service is in the provider's list of services
                if Services.lower() in [serv.strip().lower() for serv in provider["Services"]]:
                    # Check if Timings is a valid list
                    if isinstance(provider["Timings"], list) and provider["Timings"] is not None:
                        for timing_range in provider["Timings"]:
                            start_range, end_range = parse_time_string(timing_range)

                            if start_range is None or end_range is None:
                                app.logger.error("Invalid timing format in provider %s: %s", provider["ID"], timing_range)
                                continue

                            # Check if start_time is within the current timing_range
                            if start_range <= start_time < end_range:
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

@app.route('/signinmaid', methods=['POST'])
@cross_origin()
def signin_maid():
    try:
        # Extract parameters from the JSON body for POST requests
        data = request.json
        name = data.get('Name')
        mobile_number = data.get('MobileNumber')
        email_id = data.get('EmailID')
        password = data.get('Password')

        # Execute the SQL query to insert data into the maid_accountdetails table
        cursor.execute(
            "INSERT INTO maid_accountdetails (Name, MobileNumber, EmailID, Password) "
            "VALUES (?, ?, ?, ?)",
            (name, mobile_number, email_id, password)
        )
        conn.commit()

        # Return a success message
        return jsonify({"message": "Maid details added successfully"})
    except Exception as e:
        # Log the error and return an error message in case of an exception
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/signincustomer', methods=['POST'])
@cross_origin()
def sign_in_customer():
    try:
        # Extract parameters from the JSON body for POST requests
        data = request.json
        name = data.get('Name')
        mobile_number = data.get('MobileNumber')
        email_id = data.get('EmailID')
        password = data.get('Password')

        # Execute the SQL query to insert data into the customer_accountdetails table
        cursor.execute(
            "INSERT INTO customer_accountdetails (Name, MobileNumber, EmailID, Password) "
            "VALUES (?, ?, ?, ?)",
            (name, mobile_number, email_id, password)
        )
        conn.commit()

        # Return a success message
        return jsonify({"message": "Customer details added successfully"})
    except Exception as e:
        # Log the error and return an error message in case of an exception
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
