import flask
from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
import pyodbc
from datetime import time, timedelta, datetime, date
from dateutil import parser
from flask_mail import Mail, Message
from flask import make_response

app = Flask(__name__)
CORS(app) 
#, resources={r"/*": {"origins": "https://yellowsense.in/"}})
# app.config['CORS_HEADERS'] = 'Content-Type'

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
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/society_names', methods=['OPTIONS', 'GET', 'POST', 'HEAD'])
@cross_origin()
def get_society_names():
    try:
        # Execute a SQL query to retrieve society names and IDs
        cursor.execute("SELECT society_id, society_name FROM Society")
        rows = cursor.fetchall()

        # Convert the result into an array of dictionaries with id and name
        society_data = [{"id": row.society_id, "name": row.society_name} for row in rows]

        response=jsonify(society_data)  # Return JSON with id and name
        
        # Set CORS headers
        # response.headers["Access-Control-Allow-Origin"]="https://yellowsense.in/"
        response.headers["Access-Control-Allow-Methods"]= "GET, POST, OPTIONS, HEAD"
        response.headers["Access-Control-Allow-Headers"]= "Content-Type"
        return response
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
        age = data.get('age')
        languages = data.get('languages')
        Region = data.get('Region')

        # Check if the phone number already exists in the database
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM maidreg WHERE PhoneNumber = ?", (phone_number,))
        count = cursor.fetchone()[0]

        if count > 0:
            # Phone number already registered, return a message
            return jsonify({"error": "Phone number already registered"}), 400

        # Execute the stored procedure
        cursor.execute(
            "EXEC InsertMaidRegistration "
            "@AadharNumber = ?, "
            "@Name = ?, "
            "@PhoneNumber = ?, "
            "@Gender = ?, "
            "@Services = ?, "
            "@Locations = ?, "
            "@Timings = ?,"
            "@age = ?, "
            "@languages = ?, "
            "@Region = ? ",
            (aadhar_number, name, phone_number, gender, services, locations, timings, age, languages, Region)
        )
        conn.commit()
        cursor.close()

        # Return a success message
        return jsonify({"message": "Maid entry added successfully"})
    except Exception as e:
        # Log the error and return an error message in case of an exception
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/get_maid_details/<int:maid_id>', methods=['GET'])
@cross_origin()
def get_maid_details(maid_id):
    try:
        cursor.execute("SELECT * FROM maidreg WHERE ID=?", (maid_id,))
        row = cursor.fetchone()

        if row:
            column_names = [column[0] for column in cursor.description]
            maid_details = {column_names[i]: row[i] for i in range(len(column_names))}
            return jsonify(maid_details)
        else:
            return jsonify({"error": "Maid not found"})
    except pyodbc.Error as e:
        return jsonify({"error": str(e)})

@app.route('/add_payment', methods=['POST'])
@cross_origin()
def add_payment():
    try:
        data = request.json
        person_name = data.get('person_name')
        mobile_number = data.get('mobile_number')

        cursor.execute(
            "INSERT INTO paymentdetails (person_name, mobile_number) "
            "VALUES (?, ?)",
            (person_name, mobile_number)
        )
        conn.commit()

        return jsonify({"message": "Payment details added successfully"})
    except Exception as e:
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/get_all_payments', methods=['GET'])
@cross_origin()
def get_all_payments():
    try:
        cursor.execute("SELECT * FROM paymentdetails")
        rows = cursor.fetchall()

        payment_details_list = []
        for row in rows:
            payment_details = {
                "payment_id": row.payment_id,
                "person_name": row.person_name,
                "mobile_number": row.mobile_number
            }
            payment_details_list.append(payment_details)

        return jsonify({"payment_details": payment_details_list})
    except pyodbc.Error as e:
        app.logger.error("An error occurred: %s", str(e))
        return jsonify({"error": str(e)})

@app.route('/get_payment_details/<string:mobile_number>', methods=['GET'])
@cross_origin()
def get_payment_details_by_mobile_number(mobile_number):
    try:
        cursor.execute("SELECT * FROM paymentdetails WHERE mobile_number=?", (mobile_number,))
        row = cursor.fetchone()

        if row:
            payment_details = {
                "payment_id": row.payment_id,
                "person_name": row.person_name,
                "mobile_number": row.mobile_number
            }
            return jsonify(payment_details)
        else:
            return jsonify({"error": "Payment detail not found for the given mobile number"})
    except pyodbc.Error as e:
        return jsonify({"error": str(e)})

def row_to_dict(row, columns):
    return {columns[i]: row[i] for i in range(len(columns))}

@app.route('/signup', methods=['POST'])
@cross_origin()
def signup():
    try:
        # Extract parameters from the JSON body for POST requests
        data = request.json
        username = data.get('Username')
        mobile_number = data.get('MobileNumber')
        role = data.get('Role')

        if role == 'Customer':
            # Check if the mobile number is already present in accountdetails
            cursor.execute("SELECT * FROM accountdetails WHERE MobileNumber=?", (mobile_number,))
            existing_user = cursor.fetchone()

            if existing_user:
                # User already exists, return a message with status code 409 (Conflict)
                return jsonify({"error": "User already registered. Please login."}), 409

            # Insert values into accountdetails table
            cursor.execute(
                "INSERT INTO accountdetails (Username, MobileNumber, Role) "
                "VALUES (?, ?, ?)",
                (username, mobile_number, role)
            )
        else:
            # Check if the mobile number is already present in maidreg
            cursor.execute("SELECT * FROM maidreg WHERE PhoneNumber=?", (mobile_number,))
            existing_maid = cursor.fetchone()

            if existing_maid:
                # User already exists, return a message with status code 409 (Conflict)
                return jsonify({"error": "User already registered as a Servicer. Please login."}), 409

            # Insert values into maidreg table
            cursor.execute(
                "INSERT INTO maidreg (Name, PhoneNumber) "
                "VALUES (?, ?)",
                (username, mobile_number)
            )

        conn.commit()

        # Return a success message with status code 200
        return jsonify({"message": "User registration successful"}), 200

    except pyodbc.Error as e:
        app.logger.error(str(e))
        # Return an error message with status code 500
        return jsonify({"error": "Internal Server Error"}), 500
        
@app.route('/customer_login/<mobile_number>', methods=['GET'])
@cross_origin()
def login(mobile_number):
    try:
        # Execute the SQL query to check if the mobile number is present in the database
        cursor.execute(
            "SELECT * FROM accountdetails WHERE MobileNumber=?",
            (mobile_number,)
        )
        row = cursor.fetchone()

        if row:
            # If the mobile number is present, return a JSON response with "registered" set to true
            return jsonify({"Registered": True}), 200
        else:
            # If the mobile number is not present, return a JSON response with "registered" set to false
            return jsonify({"Registered": False}), 200

    except pyodbc.Error as e:
        # Return an error response with a 500 status code (Internal Server Error)
        return jsonify({"error": str(e)}), 500
        
@app.route('/serviceprovider_login/<mobile_number>', methods=['GET'])
@cross_origin()
def serviceproviderlogin(mobile_number):
    try:
        # Execute the SQL query to check if the mobile number is present in the database
        cursor.execute(
            "SELECT * FROM maidreg WHERE PhoneNumber=?",
            (mobile_number,)
        )
        row = cursor.fetchone()

        if row:
            # If the mobile number is present, return a JSON response with "registered" set to true
            return jsonify({"Registered": True}), 200
        else:
            # If the mobile number is not present, return a JSON response with "registered" set to false
            return jsonify({"Registered": False}), 200

    except pyodbc.Error as e:
        # Return an error response with a 500 status code (Internal Server Error)
        return jsonify({"error": str(e)}), 500

@app.route('/edit_user', methods=['PUT'])
@cross_origin()
def edit_user():
    try:
        # Extract parameters from the JSON body for PUT requests
        data = request.json
        user_mobile_number = data.get('user_mobile_number')
        new_name = data.get('new_name')
        new_mobile_number = data.get('new_mobile_number')
        new_email = data.get('new_email')

        # Check if the user with the given mobile number exists
        cursor.execute('SELECT * FROM accountdetails WHERE MobileNumber = ?', (user_mobile_number,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Begin the transaction
        cursor.execute("BEGIN TRANSACTION;")

        # Update the related records in the "ServiceBookings" table
        if new_mobile_number is not None:
            cursor.execute(
                "UPDATE ServiceBookings SET user_phone_number = ? WHERE user_phone_number = ?",
                (new_mobile_number, user_mobile_number)
            )
            conn.commit()

        # Update the user profile based on the mobile number in the "accountdetails" table
        update_query_accountdetails = "UPDATE accountdetails SET"
        update_params_accountdetails = []

        if new_name is not None:
            update_query_accountdetails += " Username = ?,"
            update_params_accountdetails.append(new_name)

        if new_mobile_number is not None:
            update_query_accountdetails += " MobileNumber = ?,"
            update_params_accountdetails.append(new_mobile_number)

        if new_email is not None:
            update_query_accountdetails += " Email = ?,"
            update_params_accountdetails.append(new_email)

        # Remove the trailing comma if there are updates
        if update_params_accountdetails:
            update_query_accountdetails = update_query_accountdetails.rstrip(',')
            update_query_accountdetails += " WHERE MobileNumber = ?"
            update_params_accountdetails.append(user_mobile_number)

            cursor.execute(update_query_accountdetails, tuple(update_params_accountdetails))
            conn.commit()

            # Update the user_name or user_email in the "ServiceBookings" table if they are updated
            update_query_servicebookings = "UPDATE ServiceBookings SET"
            update_params_servicebookings = []

            if new_name is not None:
                update_query_servicebookings += " user_name = ?,"
                update_params_servicebookings.append(new_name)

            if new_email is not None:
                update_query_servicebookings += " user_email = ?,"
                update_params_servicebookings.append(new_email)

            # Remove the trailing comma if there are updates
            if update_params_servicebookings:
                update_query_servicebookings = update_query_servicebookings.rstrip(',')
                update_query_servicebookings += " WHERE user_phone_number = ?"
                update_params_servicebookings.append(new_mobile_number)

                cursor.execute(update_query_servicebookings, tuple(update_params_servicebookings))
                conn.commit()

        # Commit the transaction
        cursor.execute("COMMIT TRANSACTION;")

        # Return a success message
        return jsonify({"message": "User profile updated successfully"})
    except Exception as e:
        # Rollback the transaction in case of an exception
        cursor.execute("ROLLBACK TRANSACTION;")

        # Log the error and return an error message
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/delete_maid_by_mobile', methods=['DELETE'])
@cross_origin()
def delete_maid_by_mobile():
    try:
        # Extract the mobile number from the request parameters
        mobile_number = request.args.get('mobile_number')

        # Check if the mobile number is provided
        if not mobile_number:
            return jsonify({"error": "Missing mobile_number parameter"}), 400

        # Check if the maid with the given mobile number exists
        cursor.execute('SELECT * FROM maidreg WHERE PhoneNumber = ?', (mobile_number,))
        maid = cursor.fetchone()

        if not maid:
            return jsonify({"error": "Maid not found"}), 404

        # Delete the maid record
        cursor.execute('DELETE FROM maidreg WHERE PhoneNumber = ?', (mobile_number,))
        conn.commit()

        return jsonify({"message": "Maid deleted successfully"})
    except Exception as e:
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500
        
@app.route('/update_maid_by_mobile', methods=['PUT'])
@cross_origin()
def update_maid_by_mobile():
    try:
        # Extract parameters from the JSON body for PUT requests
        data = request.json
        user_mobile_number = data.get('user_mobile_number')
        new_mobile_number = data.get('new_mobile_number')
        name = data.get('name')
        services = data.get('services')
        locations = data.get('locations')
        timings = data.get('timings')
        aadhar_number = data.get('aadhar_number')
        rating = data.get('rating')
        languages = data.get('languages')
        second_category = data.get('second_category')
        region = data.get('region')
        description = data.get('description')
        sunday_availability = data.get('sunday_availability')
        years_of_experience = data.get('years_of_experience')
        age = data.get('age')
        gender=data.get('gender')
        pan_card=data.get('pan_card')

        # Check if the user with the given mobile number exists
        cursor.execute('SELECT * FROM maidreg WHERE PhoneNumber = ?', (user_mobile_number,))
        user = cursor.fetchone()
        print(f"user: {user}")

        if not user:
            print(f"User not found in maidreg table for mobile number: {user_mobile_number}")
            return jsonify({"error": "User not found"}), 404

        # Begin the transaction
        cursor.execute("BEGIN TRANSACTION;")

        # Update the user profile based on the mobile number
        update_query = "UPDATE maidreg SET"
        update_params = []


        if new_mobile_number is not None:
            update_query += " PhoneNumber = ?,"
            update_params.append(new_mobile_number)
        
        if name is not None:
            update_query += " Name = ?,"
            update_params.append(data['name'])

        if services is not None:
            update_query += " Services = ?,"
            update_params.append(data['services'])

        if locations is not None:
            update_query += " Locations = ?,"
            update_params.append(data['locations'])

        if timings is not None:
            update_query += " Timings = ?,"
            update_params.append(data['timings'])

        if aadhar_number is not None:
            update_query += " AadharNumber = ?,"
            update_params.append(data['aadhar_number'])

        if rating is not None:
            update_query += " RATING = ?,"
            update_params.append(data['rating'])

        if languages is not None:
            update_query += " languages = ?,"
            update_params.append(data['languages'])

        if second_category is not None:
            update_query += " second_category = ?,"
            update_params.append(data['second_category'])

        if region is not None:
            update_query += " Region = ?,"
            update_params.append(data['region'])

        if description is not None:
            update_query += " description = ?,"
            update_params.append(data['description'])        
        
        if sunday_availability is not None:
            update_query += " Sunday_availability = ?,"
            update_params.append(data['sunday_availability'])  
        
        if years_of_experience is not None:
            update_query += " years_of_experience = ?,"
            update_params.append(data['years_of_experience']) 

        if age is not None:
            update_query += " age = ?,"
            update_params.append(data['age'])

        if gender is not None:
            update_query += " Gender = ?,"
            update_params.append(data['gender'])
        
        if pan_card is not None:
            update_query += " pancardnumber = ?,"
            update_params.append(data['pan_card'])


        # Remove the trailing comma if there are updates
        if update_params:
            update_query = update_query.rstrip(',')
            update_query += " WHERE PhoneNumber = ?"
            update_params.append(user_mobile_number)

            cursor.execute(update_query, tuple(update_params))

        if name is not None and new_mobile_number is not None:
            cursor.execute(
                "UPDATE ServiceBookings SET provider_name = ?, provider_phone_number = ? WHERE provider_phone_number = ?",
                (name, new_mobile_number, user_mobile_number)
            )
            conn.commit()

        # Commit the transaction
        cursor.execute("COMMIT TRANSACTION;")

        # Return a success message
        return jsonify({"message": "User profile updated successfully"})
    except pyodbc.IntegrityError as e:
        # Rollback the transaction in case of a primary key violation
        cursor.execute("ROLLBACK TRANSACTION;")
        app.logger.error(str(e))
        return jsonify({"error": "Duplicate phone number in maidreg table"}), 500
    except Exception as e:
        # Rollback the transaction in case of an exception
        cursor.execute("ROLLBACK TRANSACTION;")
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500
        
@app.route('/get_customer/<string:mobile_number>', methods=['GET'])
@cross_origin()
def customer_details(mobile_number):
    try:

        # SQL query to retrieve customer details excluding the password
        query = f"SELECT UserID, Username, MobileNumber FROM accountdetails WHERE MobileNumber = '{mobile_number}'"
        
        # Execute the query
        cursor.execute(query)
        
        # Fetch the results
        customer_details = cursor.fetchone()

        if customer_details:
            # Convert results to a dictionary for JSON response
            result = {
                'UserID': customer_details[0],
                'Username': customer_details[1],
                'MobileNumber': customer_details[2],
            }
            return jsonify(result)
        else:
            return jsonify({'message': 'Customer not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/customer-booking-details/<customer_mobile_number>', methods=['GET'])
@cross_origin()
def get_customer_booking_details(customer_mobile_number):
    try:
        # Query booking details for a specific customer from ServiceBookings table
        booking_sql_query = f"SELECT * FROM ServiceBookings WHERE user_phone_number = '{customer_mobile_number}' ORDER BY id DESC"
        cursor.execute(booking_sql_query)
        booking_details = cursor.fetchall()

        # Convert the query result to a list of dictionaries for JSON response
        booking_details_list = [dict(zip([column[0] for column in cursor.description], row)) for row in booking_details]

        if not booking_details_list:
            return jsonify({'message': 'No booking details found for the customer'}), 404

        # Process booking details to create provider details list
        provider_details_list = []
        for booking in booking_details_list:
            provider_details_dict = {
                'provider_name': booking['provider_name'],
                'service_type': booking['service_type'],
                'status': booking['status'],
                'ServiceStatus' : booking['ServiceStatus'],
                'booking_id': booking['id']
            }

            # If apartment is empty, use Region as the location key
            if not booking['apartment']:
                provider_details_dict['location'] = booking['Region']
            else:
                # If apartment has a value, use it as the location key
                provider_details_dict['location'] = booking['apartment']

            provider_details_list.append(provider_details_dict)

        return jsonify({'provider_details': provider_details_list})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


def convert_date_format(date_str):
    try:
        # Try parsing as 'YYYY-MM-DD' format
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        try:
            # Try parsing as 'DD-MM-YYYY' format
            return datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y-%m-%d')
        except ValueError:
            # If parsing fails, raise an error or handle it as needed
            raise ValueError(f"Invalid date format: {date_str}")
            
def convert_time_to_string(time_obj, use_12_hour_format=True):
    if use_12_hour_format:
        return time_obj.strftime('%I:%M %p')
    else:
        return time_obj.strftime('%H:%M')

@app.route('/booking', methods=['POST'])
@cross_origin()
def booking():
    cursor = conn.cursor()

    try:
        data = request.json
        provider_mobile_number = data.get('provider_mobile_number')

        # Check if the provider_mobile_number is valid
        cursor.execute('SELECT * FROM maidreg WHERE PhoneNumber = ?', (provider_mobile_number,))
        provider = cursor.fetchone()

        if not provider:
            return jsonify({"error": "Invalid service provider"}), 400

        customer_mobile_number = data.get('customer_mobile_number')
        status = data.get('status')  # New field for customer status

        # Check if the status is valid (confirm or cancel)
        if status not in ['confirm', 'cancel']:
            return jsonify({"error": "Invalid customer status"}), 400

        if status == 'cancel':
            return jsonify({"message": "Booking canceled"})

        # Get the username of the customer
        cursor.execute('SELECT Username FROM accountdetails WHERE MobileNumber = ?', (customer_mobile_number,))
        customer_username_result = cursor.fetchone()

        # Check if the result is not None before accessing the attribute
        if customer_username_result:
            customer_username = customer_username_result.Username

            # Get the name of the service provider
            provider_name = provider.Name

            start_time = data.get('start_time')
            start_date = data.get('start_date')  # Assuming you still need this field
            service = data.get('service_type')  # Assuming you still need this field
            apartment = data.get('apartment')
            area = data.get('area')
            user_address = data.get('user_address')  # New field for the apartment area

            # Insert into ServiceBookings and retrieve the last inserted ID
            cursor.execute('INSERT INTO ServiceBookings (user_phone_number, provider_phone_number, customer_status, user_name, provider_name, start_time, StartDate, service_type, apartment, Region, user_address) OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (customer_mobile_number, provider_mobile_number, status, customer_username, provider_name, start_time, start_date, service, apartment, area, user_address))
            last_inserted_id = cursor.fetchone().id
            conn.commit()

            query = '''
                SELECT
                    sb.id AS booking_id,
                    sb.user_name,
                    sb.provider_name,
                    sb.provider_phone_number,
                    sb.start_time,
                    sb.StartDate,
                    sb.service_type,
                    sb.apartment,
                    sb.Region,  -- Added Region field
                    sb.user_address,
                    sp.Services AS service_provider_services,
                    sp.Locations AS service_provider_locations,
                    ad.MobileNumber AS user_phone_number,
                    sb.customer_status
                FROM
                    ServiceBookings sb
                    INNER JOIN maidreg sp ON sb.provider_phone_number = sp.PhoneNumber
                    INNER JOIN accountdetails ad ON sb.user_phone_number = ad.MobileNumber
                WHERE
                    sb.id = ?
            '''

            cursor.execute(query, (last_inserted_id,))
            row = cursor.fetchone()

            if row:
                booking_details = {
                    "booking_id": row.booking_id,
                    "service_provider_details": {
                        "service_provider_name": row.provider_name,
                        "provider_phone_number": row.provider_phone_number,
                        "service_provider_services": row.service_provider_services.split(','),
                        "service_provider_locations": row.service_provider_locations.split(',')
                    },
                    "user_details": {
                        "user_name": row.user_name,
                        "user_phone_number": row.user_phone_number,
                        "user_address": row.user_address
                    },
                    "start_time": row.start_time,
                    "start_date": row.StartDate,
                    "service_type": row.service_type,
                    "apartment": row.apartment,
                    "area": row.Region,  # Added area field
                    "customer_status": row.customer_status
                }

                return jsonify(booking_details)
            else:
                return jsonify({"error": "Booking not found"})
        else:
            return jsonify({"error": "User not found"})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        cursor.close()
        
@app.route('/getcustomermaiddetails', methods=['GET'])
@cross_origin()
def get_customer_maid_details():
    try:
        data = request.args

        customer_mobile_number = data.get('customer_mobile_number')
        provider_mobile_number = data.get('provider_mobile_number')

        # Fetch provider details from MaidReg based on the provided mobile number
        sql_query_provider = f"SELECT ID, Name, PhoneNumber, Locations, Region, Services FROM maidreg WHERE PhoneNumber = '{provider_mobile_number}'"
        cursor.execute(sql_query_provider)
        provider_details = cursor.fetchone()

        # Fetch customer details from AccountDetails based on the provided mobile number
        sql_query_customer = f"SELECT UserID, Username, MobileNumber FROM accountdetails WHERE MobileNumber = '{customer_mobile_number}'"
        cursor.execute(sql_query_customer)
        customer_details = cursor.fetchone()

        if provider_details and customer_details:
            # Process and return the details
            return jsonify({
                'message': 'Details fetched successfully!',
                'customer_details': {
                    'UserID': customer_details.UserID,
                    'Username': customer_details.Username,
                    'MobileNumber': customer_details.MobileNumber,
                },
                'provider_details': {
                    'ID': provider_details.ID,
                    'Name': provider_details.Name,
                    'PhoneNumber': provider_details.PhoneNumber,
                    'Locations': provider_details.Locations,
                    'Region': provider_details.Region,
                    'Services': provider_details.Services,
                }
            }), 200
        else:
            return jsonify({'message': 'Provider or Customer not found!'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/booking_accept_reject', methods=['POST'])
@cross_origin()
def booking_accept_reject():
    data = request.get_json()

    provider_phone = data.get('provider_phone')
    action = data.get('action')

    # Execute raw SQL query to fetch the booking
    sql_query = f"SELECT TOP 1 * FROM ServiceBookings WHERE provider_phone_number = '{provider_phone}' AND (status IS NULL OR status = 'pending');" 
    cursor.execute(sql_query)
    booking = cursor.fetchone()
    if booking:
        if action == 'accept':
            # Execute raw SQL query to update the booking status
            update_query = f"UPDATE ServiceBookings SET status = 'accept' WHERE id = {booking.id};"
            cursor.execute(update_query)
            provider_details_query = f"SELECT * FROM maidreg WHERE PhoneNumber = '{provider_phone}';"
            cursor.execute(provider_details_query)
            provider_details = cursor.fetchone()

            conn.commit()  # Commit the changes to the database

            if provider_details:
                # Return booking confirmation message along with provider details
                response = {
                    'message': 'Booking confirmed',
                    'provider_details': {
                        'name': provider_details.Name,
                        'gender': provider_details.Gender,
                        'phone_number': provider_details.PhoneNumber,
                        'services': provider_details.Services,
                        'locations': provider_details.Locations,
                        'Region': provider_details.Region,
                        'timings': provider_details.Timings
                    }
                }
                return jsonify(response)
            else:
                return jsonify({'message': 'Provider details not found'})
        elif action == 'reject':
            # Execute raw SQL query to update the booking status
            update_query = f"UPDATE ServiceBookings SET status = 'reject' WHERE id = {booking.id};"
            cursor.execute(update_query)
            conn.commit()
            return jsonify({'message': 'Booking rejected'})
    else:
        return jsonify({'message': 'Booking not found or already processed'})

@app.route('/customer/ongoing_requests', methods=['GET'])
@cross_origin()
def customer_ongoing_requests():
    customer_mobile = request.args.get('customer_mobile')

    # Execute raw SQL query to count ongoing (accepted) requests for the customer
    ongoing_query = f"SELECT COUNT(*) FROM ServiceBookings WHERE user_phone_number = '{customer_mobile}' AND status = 'accept';"
    cursor.execute(ongoing_query)
    ongoing_count = cursor.fetchone()[0]

    response = {
        'ongoing_requests': ongoing_count
    }

    return jsonify(response)

@app.route('/customer/cancelled_requests', methods=['GET'])
@cross_origin()
def customer_cancelled_requests():
    customer_mobile = request.args.get('customer_mobile')

    # Execute raw SQL query to count canceled (rejected) requests for the customer
    cancelled_query = f"SELECT COUNT(*) FROM ServiceBookings WHERE user_phone_number = '{customer_mobile}' AND status = 'reject';"
    cursor.execute(cancelled_query)
    cancelled_count = cursor.fetchone()[0]

    response = {
        'cancelled_requests': cancelled_count
    }

    return jsonify(response)
    
@app.route('/serviceprovider/requests', methods=['GET'])
@cross_origin()
def get_requests():
    provider_mobile = request.args.get('provider_mobile')
    request_type = request.args.get('request_type')  # 'total', 'accepted', or 'rejected'

    if request_type is None:
        # If request_type is not provided, return counts for all types
        total_count = get_request_count(provider_mobile, 'total')
        accepted_count = get_request_count(provider_mobile, 'accept')
        rejected_count = get_request_count(provider_mobile, 'reject')

        response = {
            'total_requests': total_count,
            'accepted_requests': accepted_count,
            'rejected_requests': rejected_count
        }
    elif request_type == 'total' or request_type == 'accepted' or request_type == 'reject':
        # If request_type is provided, return count for the specified type
        count = get_request_count(provider_mobile, request_type)

        response = {
            f'{request_type}_requests': count
        }
    else:
        return jsonify({'error': 'Invalid request_type'}), 400

    return jsonify(response)
    
def get_request_count(provider_mobile, request_type):
    if request_type == 'total':
        status_condition = ""  # Empty condition to get the total count
    elif request_type == 'accept':
        status_condition = "status = 'accept'"
    elif request_type == 'reject':
        status_condition = "status = 'reject'"
    else:
        raise ValueError('Invalid request_type')

    # Execute raw SQL query to count requests based on the specified type
    if request_type == 'total':
        query = f"SELECT COUNT(*) FROM ServiceBookings WHERE provider_phone_number = '{provider_mobile}';"
    else:
        query = f"SELECT COUNT(*) FROM ServiceBookings WHERE provider_phone_number = '{provider_mobile}' AND {status_condition};"

    cursor.execute(query)
    request_count = cursor.fetchone()[0]

    return request_count

@app.route('/serviceprovider/requests_details', methods=['GET'])
@cross_origin()
def get_requests_details():
    provider_mobile = request.args.get('provider_mobile')
    request_status = request.args.get('request_status')  # 'accepted', 'rejected', or 'total'

    if request_status not in ['accept', 'reject', 'total']:
        return jsonify({'error': 'Invalid request_status'}), 400

    # Execute raw SQL query to retrieve details based on the specified status
    if request_status == 'total':
        query = f"SELECT user_name, user_address, user_phone_number, apartment, service_type FROM ServiceBookings WHERE provider_phone_number = '{provider_mobile}';"
    else:
        status_condition = f"status = '{request_status}'"
        query = f"SELECT user_name, user_address, user_phone_number, apartment, service_type FROM ServiceBookings WHERE provider_phone_number = '{provider_mobile}' AND {status_condition};"

    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    
    # Convert each row to a dictionary for JSON serialization
    rows = cursor.fetchall()
    request_details = [dict(zip(columns, row)) for row in rows]

    response = {
        f'{request_status}_requests': request_details
    }

    return jsonify(response)

@app.route('/profile_details', methods=['POST'])
@cross_origin()
def profile_details():
    try:
        data = request.json
        user_mobile_number = data.get('user_mobile_number')

        cursor.execute("BEGIN TRANSACTION;")

        # Update or insert into maidreg
        cursor.execute('SELECT * FROM maidreg WHERE PhoneNumber = ?', (user_mobile_number,))
        user_in_maidreg = cursor.fetchone()

        if user_in_maidreg:
            update_query_maidreg = """
                UPDATE maidreg
                SET Name = COALESCE(?, Name),
                    Services = COALESCE(?, Services),
                    Locations = COALESCE(?, Locations),
                    Timings = COALESCE(?, Timings),
                    AadharNumber = COALESCE(?, AadharNumber),
                    RATING = COALESCE(?, RATING),
                    languages = COALESCE(?, languages),
                    second_category = COALESCE(?, second_category),
                    Region = COALESCE(?, Region),
                    description = COALESCE(?, description),
                    Sunday_availability = COALESCE(?, Sunday_availability),
                    years_of_experience = COALESCE(?, years_of_experience),
                    age = COALESCE(?, age),
                    Gender = COALESCE(?, Gender),
                    pancardnumber = COALESCE(?, pancardnumber)
                WHERE PhoneNumber = ?
            """
            cursor.execute(
                update_query_maidreg,
                (
                    data.get('name'),
                    data.get('services'),
                    data.get('locations'),
                    data.get('timings'),
                    data.get('aadhar_number'),
                    data.get('rating'),
                    data.get('languages'),
                    data.get('second_category'),
                    data.get('region'),
                    data.get('description'),
                    data.get('sunday_availability'),
                    data.get('years_of_experience'),
                    data.get('age'),
                    data.get('gender'),
                    data.get('pan_card'),
                    user_mobile_number,
                )
            )
            conn.commit()
        else:
            insert_query_maidreg = """
                INSERT INTO maidreg (PhoneNumber, Name, Services, Locations, Timings, AadharNumber , RATING ,languages, second_category , Region , description , Sunday_availability ,years_of_experience, age , Gender , pancardnumber)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(
                insert_query_maidreg,
                (
                    user_mobile_number,
                    data.get('name'),
                    data.get('services'),
                    data.get('locations'),
                    data.get('timings'),
                    data.get('aadhar_number'),
                    data.get('rating'),
                    data.get('languages'),
                    data.get('second_category'),
                    data.get('region'),
                    data.get('description'),
                    data.get('sunday_availability'),
                    data.get('years_of_experience'),
                    data.get('age'),
                    data.get('gender'),
                    data.get('pan_card'),
                )
            )
            conn.commit()

        cursor.execute("COMMIT TRANSACTION;")

        return jsonify({"message": "User profile updated or created successfully"})
    except pyodbc.IntegrityError as e:
        cursor.execute("ROLLBACK TRANSACTION;")
        app.logger.error(str(e))
        return jsonify({"error": "Duplicate phone number in maidreg or accountdetails table"}), 500
    except Exception as e:
        cursor.execute("ROLLBACK TRANSACTION;")
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500
        
        
@app.route('/area_names', methods=['GET'])
@cross_origin()
def get_area_names():
    try:
        # Execute a SQL query to retrieve area IDs and names
        cursor.execute("SELECT AreaID, AreaName FROM Area")
        rows = cursor.fetchall()

        # Convert the result into an array of dictionaries with id and name
        area_data = [{"id": row.AreaID, "name": row.AreaName} for row in rows]

        return jsonify(area_data)  # Return JSON with id and name
    except pyodbc.Error as e:
        return jsonify({"error": str(e)})
def parse_time_string(time_str):
    try:
        start_str, end_str = time_str.split('-')
        start_time = parser.parse(start_str).time()
        end_time = parser.parse(end_str).time()

        # Check if end_time is less than start_time, indicating spanning two days
        if end_time < start_time:
            # Increment the day for end_time using timedelta
            end_time = (datetime.combine(datetime.min, end_time) + timedelta(days=1)).time()

        return start_time, end_time
    except ValueError:
        return None, None
def find_matching_service_providers(locations, services, start_time_str, region):
    try:
        # Check if services is empty
        if not services:
            return {"error": "'services' is mandatory"}

        # Initial part of the query
        query = """
            SELECT ID, Name, Gender, Services, Locations,PhoneNumber, Timings, RATING, Region, Image
            FROM maidreg
            WHERE CHARINDEX(?, Services COLLATE SQL_Latin1_General_CP1_CI_AS) > 0
            AND Status = 'available'
        """

        # Check if locations is provided
        if locations:
            query += " AND CHARINDEX(?, Locations) > 0"

        # Check if region is provided
        if region is not None:
            query += " AND CHARINDEX(?, region) > 0"

        # Order by rating
        query += " ORDER BY RATING DESC"

        if locations and region:
            cursor.execute(query, (services, locations, region))
        elif locations:
            cursor.execute(query, (services, locations))
        else:
            cursor.execute(query, (services, region))
        

        rows = cursor.fetchall()

        # rest of the code remains unchanged...

        start_time = parser.parse(f'1900-01-01 {start_time_str}').time()
        if start_time is None:
            app.logger.error("Invalid start_time format: %s", start_time_str)
            return {"error": "Invalid start_time format"}

        matching_providers = []
        for row in rows:
            row_services = [service.strip("' ") for service in (row.Services.split(',') if row.Services else [])]

            # Check if row_locations is not None before processing
            if row.Locations:
                row_locations = [location.strip("' ") for location in row.Locations.split(',')]
            else:
                row_locations = []

            # Check if row.Region is not None before processing
            if row.Region:
                row_region = [region.strip("' ") for region in row.Region.split(',')]
            else:
                row_region = []

            timings = [timing.strip("' ") for timing in (row.Timings.split(',') if row.Timings else [])]

            # if row_locations and any(locations.strip().lower() in loc.strip("' ").lower() for loc in row_locations):
            if services.lower() in [serv.strip().lower() for serv in row_services]:
                if timings:
                    for timing_range in timings:
                        start_range, end_range = parse_time_string(timing_range)

                        if start_range is None or end_range is None:
                            app.logger.error("Invalid timing format in provider %s: %s", row.ID, timing_range)
                            continue

                        if start_range <= start_time < end_range:
                            matching_providers.append({
                                "ID": row.ID,
                                "Name": row.Name,
                                "Gender": row.Gender,
                                "PhoneNumber":row.PhoneNumber,
                                "Services": row_services,
                                "Locations": row_locations,
                                "Region": row_region,
                                "Timings": timings,
                                "Image": row.Image,
                                "Rating": row.RATING
                            })
                            break
                else:
                    app.logger.error("Invalid Timings format in provider %s: %s", row.ID, timings)

        return matching_providers

    except pyodbc.Error as e:
        app.logger.error("Error querying service providers: %s", e)
        return {"error": "Error querying service providers"}
        
@app.route('/get_matching_service_providers', methods=['GET', 'POST'])
@cross_origin()
def get_matching_providers():
    if request.method == 'GET':
        locations = request.args.get('Locations')
        region = request.args.get('Region')
        services = request.args.get('Services')
        date = request.args.get('date')
        start_time = request.args.get('start_time')
    elif request.method == 'POST':
        data = request.json
        locations = data.get('Locations')
        region = data.get('Region')
        services = data.get('Services')
        date = data.get('date')
        start_time = data.get('start_time')
    else:
        return jsonify({"error": "Unsupported method"})
    
    if locations is None and region is None and not services or not date or not start_time:
        return jsonify({"error": "Either 'locations' or 'region' is mandatory"})

    matching_providers = find_matching_service_providers(locations, services, start_time,region)

    if matching_providers:
        return jsonify({"providers": matching_providers})
    else:
        return jsonify({"error": "No matching service providers found"})

@app.route('/get_maid_by_phone', methods=['GET'])
@cross_origin()
def get_maid_by_phone():
    try:
        phone_number = request.args.get('phone_number')

        if not phone_number:
            return jsonify({"error": "Missing 'phone_number' parameter"}), 400

        # Check if the maid with the given phone number exists
        cursor.execute('SELECT * FROM maidreg WHERE PhoneNumber = ?', (phone_number,))
        maid = cursor.fetchone()

        if not maid:
            return jsonify({"error": "Maid not found for the provided phone number"}), 404

        # Convert the result to a dictionary for JSON response
        maid_details = {
            "ID": maid.ID,
            "Name": maid.Name,
            "Gender": maid.Gender,
            "PhoneNumber": maid.PhoneNumber,
            "Age": maid.Age,
            "Services": maid.Services.split(',') if maid.Services else [],
            "Locations": maid.Locations.split(',') if maid.Locations else [] if maid.Locations is not None else [],
            "Timings": maid.Timings.split(',') if maid.Timings else [],
            "Rating": maid.RATING,
            "Region": maid.Region.split(',') if maid.Region else [] if maid.Region is not None else [],
            "Languages": maid.Languages.split(',') if maid.Languages else [] if maid.Languages is not None else [],
            "AadharNumber": maid.AadharNumber,
            "Years_of_Experience": maid.Years_of_Experience,
            "Sunday_Availability": maid.Sunday_Availability,
            "Description": maid.Description,
            # ... (add other fields as needed)
        }
        
        return jsonify({"maid_details": maid_details})

    except Exception as e:
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/make_call', methods=['GET'])
def make_call():
    import requests

    # Replace these values with your Exotel API credentials and other details
    api_key = "3ccb0ac3919ccea8ecf9a4d5de2ed92633ba63795fc4755a"
    api_token = "3d26731864f6daf1a845b993e2fda685fe158a60ed003f04"
    subdomain = "api.exotel.com"
    account_sid = "yellowsense3"
    to_number = "02248964153"  # The phone number that you want to call
    ivr_app_id = "752086"

    # Get 'from_number' from the query parameters in the URL
    from_number = request.args.get('from_number', '')

    if not from_number:
        return jsonify({"error": "Missing 'from_number' parameter in the URL"}), 400

    # Prepare data for the API request
    data = {
        'From': from_number,
        'To': to_number,
        'CallerId': to_number,
        'Url': f"http://{subdomain}/{account_sid}/exoml/start_voice/{ivr_app_id}",
    }

    # Construct the API endpoint
    api_endpoint = f"https://{api_key}:{api_token}@{subdomain}/v1/Accounts/{account_sid}/Calls/connect.json"

    # Make the API request
    response = requests.post(api_endpoint, data=data)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # You may want to store the 'Sid' from the response for future reference or logging
        call_sid = response.json().get('Call', {}).get('Sid')
        return jsonify({"message": "Outgoing call initiated successfully.", "call_sid": call_sid}), 200
    else:
        return jsonify({"error": f"Error: {response.status_code}, {response.text}"}), response.status_code

@app.route('/get_latest_details', methods=['GET'])
@cross_origin()
def get_latest_details():
    try:
        mobile_number = request.args.get('mobile_number')

        print(f"Received request for mobile_number: {mobile_number}")

        cursor = conn.cursor()

        # Query to retrieve the latest 5 details for the specified mobile number
        query = (
            "SELECT TOP 5 user_name, service_type, apartment, StartDate, start_time, status "
            "FROM ServiceBookings "
            "WHERE provider_phone_number = ? "
            "ORDER BY created_at DESC;"
        )

        cursor.execute(query, mobile_number)
        latest_details = cursor.fetchall()

        if latest_details:
            # Convert the pyodbc.Row objects to a list of dictionaries
            result = []
            for details in latest_details:
                details_dict = dict(zip([column[0] for column in cursor.description], details))
                # Format the StartDate field using strftime
                details_dict['StartDate'] = details_dict['StartDate'].strftime('%Y-%m-%d')  # Adjust the format as needed
                result.append(details_dict)

            print(f"Latest details for mobile_number {mobile_number}: {result}")
            return jsonify({'latest_details': result})
        else:
            # If there are no latest details, retrieve all details (up to 5)
            all_details_query = (
                "SELECT user_name, service_type, apartment, StartDate, start_time, status "
                "FROM ServiceBookings "
                "WHERE provider_phone_number = ? "
                "ORDER BY created_at DESC;"
            )

            cursor.execute(all_details_query, mobile_number)
            all_details = cursor.fetchall()

            if all_details:
                # Convert the pyodbc.Row objects to a list of dictionaries
                result = []
                for details in all_details:
                    details_dict = dict(zip([column[0] for column in cursor.description], details))
                    # Format the StartDate field using strftime
                    details_dict['StartDate'] = details_dict['StartDate'].strftime('%Y-%m-%d')  # Adjust the format as needed
                    result.append(details_dict)

                print(f"All available details for mobile_number {mobile_number}: {result}")
                return jsonify({'latest_details': result})
            else:
                print(f"No details found for mobile_number {mobile_number}")
                return jsonify({'error': 'No details found for the provided mobile number'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/insertaddress', methods=['POST'])
@cross_origin()
def insert_address():
    try:
        # Assuming JSON payload with optional keys: houseno, roadname, pincode, Name, new_mobilenumber
        details = request.json
         # Extract other details
        registermobilenumber = details.get('registermobilenumber')
        user_name = details.get('Name', '')
        mobile_number = details.get('mobilenumber')
        # Extract individual fields from the JSON payload
        houseno = details.get('houseno', '')
        roadname = details.get('roadname', '')
        pincode = details.get('pincode', '')

        # Combine houseno, roadname, pincode into a single user_address column separated by comma
        user_address = ', '.join(filter(None, [houseno, roadname, pincode]))


        # Insert data into the ServiceBookings table
        cursor.execute("""
            INSERT INTO address
            (address, name, mobilenumber,registermobilenumber)
            VALUES (?, ?, ?, ?)
        """, (user_address, user_name, mobile_number, registermobilenumber ))
        
        conn.commit()

        return jsonify({'message': 'Details inserted successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/address_details', methods=['GET'])
@cross_origin()
def address_details():
    register_mobilenumber = request.args.get('registermobilenumber')

    if not register_mobilenumber:
        return jsonify({"error": "Missing 'registermobilenumber' parameter"}), 400

    try:
        cursor.execute("SELECT * FROM address WHERE registermobilenumber = ?", (register_mobilenumber,))
        address_details_list = cursor.fetchall()
    except pyodbc.Error as e:
        app.logger.error("Error executing SQL query: %s", e)
        return jsonify({"error": "Error executing SQL query"}), 500

    if not address_details_list:
        return jsonify([])

    # Convert the result to a list of dictionaries for JSON response
    result_list = []
    for address_details in address_details_list:
        address_parts = address_details.address.split(',')
        if len(address_parts) < 3:
            app.logger.error("Address format is incorrect: %s", address_details.address)
            continue

        result_dict = {
            "id": address_details.id,  # replace with the actual column name
            "registermobilenumber": address_details.registermobilenumber,  # replace with the actual column name
            "mobilenumber": address_details.mobilenumber,  # replace with the actual column name
            "name": address_details.name,  # replace with the actual column name
            "address": {
                "houseno": address_parts[0].strip(),
                "roadname": address_parts[1].strip(),
                "pincode": address_parts[2].strip()
            }
        }
        result_list.append(result_dict)

    return jsonify(result_list)
    
def execute_query(query, parameters=None):
    cursor.execute(query, parameters)
    return cursor.fetchone()

@app.route('/get_service_provider', methods=['GET'])
@cross_origin()
def get_service_provider():
    try:
        mobile_number = request.args.get('mobile_number')

        # Fetch all data from maidreg table
        cursor.execute("SELECT * FROM maidreg WHERE PhoneNumber = ?", (mobile_number,))
        maidreg_data = cursor.fetchone()

        if maidreg_data:
            # Convert the cursor description to a list of column names
            columns = [column[0] for column in cursor.description]

            # Create a dictionary with column names as keys and corresponding values
            serviceproviders_data = dict(zip(columns, maidreg_data))

            return jsonify({'serviceproviders': serviceproviders_data})
        else:
            return jsonify({'error': 'Service provider not found for the given mobile number'})

    except Exception as e:
        return jsonify({'error': str(e)})
        
@app.route('/exotelaccept', methods=['GET'])
def exotelaccept():
    try:
        data = request.args.to_dict()

        if not data:
            return jsonify({'error': 'No query parameters provided'}), 400

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'Time: {current_time}, status: accept, data: {data}')

        # You can process the data here as needed

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/exotelreject', methods=['GET'])
def exotelreject():
    try:
        data = request.args.to_dict()

        if not data:
            return jsonify({'error': 'No query parameters provided'}), 400

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'Time: {current_time}, status: reject, data: {data}')

        # You can process the data here as needed

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
