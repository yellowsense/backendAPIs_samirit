from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import pyodbc
from datetime import time, timedelta, datetime
from dateutil import parser
from flask_mail import Mail, Message

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
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
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

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.hostinger.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'confirmation@yellowsense.in'
app.config['MAIL_PASSWORD'] = 'Confirmation2001#'
app.config['MAIL_DEFAULT_SENDER'] = 'confirmation@yellowsense.in'
mail = Mail(app)

@app.route('/confirm_nanny_booking', methods=['POST'])
@cross_origin()
def confirm_nanny_booking():
    try:
        booking_details = request.json  # Assuming the data is sent as JSON in the request body

        # Extract relevant details from the booking data
        provider_name = booking_details.get('ProviderName')
        service_type = booking_details.get('ServiceType')
        user_name = booking_details.get('UserName')
        apartment = booking_details.get('Apartment')
        StartDate = booking_details.get('StartDate')
        start_time = booking_details.get('StartTime')
        user_email = booking_details.get('UserEmail')
        special_requirements = booking_details.get('SpecialRequirements')
        child_number = booking_details.get('ChildNumber')
        user_address = booking_details.get('UserAddress')

        cursor.execute("""
            INSERT INTO ServiceBookings
            (provider_name, service_type, user_name, apartment, StartDate, start_time, user_email,
            special_requirements, child_number, user_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (provider_name, service_type, user_name, apartment, StartDate, start_time, user_email,
              special_requirements, child_number, user_address))
        conn.commit()

        # Send confirmation email to the customer
        send_confirmation_email(
            user_email, provider_name, service_type, user_name,
            apartment, StartDate,start_time, special_requirements, child_number, user_address
        )

        # You can also send confirmation emails to the respective service providers here

        return jsonify({'message': 'Booking confirmed and email sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def send_confirmation_email(
    recipient, provider_name, service_type, user_name,
    apartment,StartDate, start_time, special_requirements, child_number, user_address
):
    subject = 'Booking Confirmation'
    
    # Format the booking details for the email body
    body = f'Dear {user_name},\n\nYour booking with {provider_name} for {service_type} has been confirmed.\n\nBooking Details:\n\n'
    body += f'Provider Name: {provider_name}\n'
    body += f'Service Type: {service_type}\n'
    body += f'User Name: {user_name}\n'
    body += f'Apartment: {apartment}\n'
    body += f'Start Date: {StartDate}\n'
    body += f'Start Time: {start_time}\n'
    body += f'Special Requirements: {special_requirements}\n'
    body += f'Child Number: {child_number}\n'
    body += f'User Address: {user_address}\n'
    
    body += '\nThank you for choosing our services!'
    body +='\nThis is an auto generated mail. Please do not reply to this mail For any further queries feel free to contact us at support@yellowsense.in '
    
     # Send to the user and orders email
    recipients = [recipient, 'orders@yellowsense.in']
    msg = Message(subject, recipients=recipients, body=body)
    mail.send(msg)

@app.route('/confirm_maid_booking', methods=['POST'])
@cross_origin()
def confirm_maid_booking():
    try:
        booking_details = request.json  # Assuming the data is sent as JSON in the request body

        # Extract relevant details from the booking data
        provider_name = booking_details.get('ProviderName')
        service_type = booking_details.get('ServiceType')
        user_name = booking_details.get('UserName')
        apartment = booking_details.get('Apartment')
        StartDate = booking_details.get('StartDate')
        start_time = booking_details.get('StartTime')
        user_email = booking_details.get('UserEmail')
        special_requirements = booking_details.get('SpecialRequirements')
        house_size = booking_details.get('HouseSize')
        complete_address = booking_details.get('CompleteAddress')
        user_phone_number = booking_details.get('UserPhoneNumber')
        
        cursor.execute("""
            INSERT INTO ServiceBookings
            (provider_name, service_type, user_name, apartment, StartDate, start_time, user_email,
            special_requirements, house_size, complete_address, user_phone_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (provider_name, service_type, user_name, apartment, StartDate, start_time, user_email,
              special_requirements, house_size, complete_address, user_phone_number))
        conn.commit()

        # Send confirmation email to the customer
        send_maid_confirmation_email(
            user_email, provider_name, service_type, user_name,
            apartment,StartDate, start_time, special_requirements, house_size, complete_address, user_phone_number
        )

        return jsonify({'message': 'Maid service booking confirmed and email sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def send_maid_confirmation_email(
    recipient, provider_name, service_type, user_name,
    apartment,StartDate, start_time, special_requirements, house_size, complete_address, user_phone_number
):
    subject = 'Maid Service Booking Confirmation'
    
    # Format the booking details for the email body
    body = f'Dear {user_name},\n\nYour maid service booking with {provider_name} has been confirmed.\n\nBooking Details:\n\n'
    body += f'Provider Name: {provider_name}\n'
    body += f'Service Type: {service_type}\n'
    body += f'User Name: {user_name}\n'
    body += f'Apartment: {apartment}\n'
    body += f'Start Date: {StartDate}\n'
    body += f'Start Time: {start_time}\n'
    body += f'Special Requirements: {special_requirements}\n'
    body += f'House Size: {house_size}\n'
    body += f'Complete Address: {complete_address}\n'
    body += f'User Phone Number: {user_phone_number}\n'
    
    body += '\nThank you for choosing our services!'
    body +='\nThis is an auto generated mail. Please do not reply to this mail For any further queries feel free to contact us at support@yellowsense.in '

    
     # Send to the user and orders email
    recipients = [recipient, 'orders@yellowsense.in']
    msg = Message(subject, recipients=recipients, body=body)
    mail.send(msg)

@app.route('/confirm_cook_booking', methods=['POST'])
@cross_origin()
def confirm_cook_booking():
    try:
        booking_details = request.json  # Assuming the data is sent as JSON in the request body

        # Extract relevant details from the booking data
        provider_name = booking_details.get('ProviderName')
        service_type = booking_details.get('ServiceType')
        user_name = booking_details.get('UserName')
        apartment = booking_details.get('Apartment')
        StartDate = booking_details.get('StartDate')
        start_time = booking_details.get('StartTime')
        user_email = booking_details.get('UserEmail')
        special_requirements = booking_details.get('SpecialRequirements')
        food_preferences = booking_details.get('FoodPreferences')
        user_address = booking_details.get('UserAddress')
        user_phone_number = booking_details.get('UserPhoneNumber')

        cursor.execute("""
            INSERT INTO ServiceBookings
            (provider_name, service_type, user_name, apartment, StartDate, start_time, user_email,
            special_requirements, food_preferences, user_address, user_phone_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (provider_name, service_type, user_name, apartment, StartDate, start_time, user_email,
              special_requirements, food_preferences, user_address, user_phone_number))
        conn.commit()

        # Send confirmation email to the customer
        send_cook_confirmation_email(
            user_email, provider_name, service_type, user_name,
            apartment,StartDate, start_time, special_requirements, food_preferences, user_address, user_phone_number
        )

        return jsonify({'message': 'Cook service booking confirmed and email sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def send_cook_confirmation_email(
    recipient, provider_name, service_type, user_name,
    apartment,StartDate, start_time, special_requirements, food_preferences, user_address, user_phone_number
):
    subject = 'Cook Service Booking Confirmation'
    
    # Format the booking details for the email body
    body = f'Dear {user_name},\n\nYour cook service booking with {provider_name} has been confirmed.\n\nBooking Details:\n\n'
    body += f'Provider Name: {provider_name}\n'
    body += f'Service Type: {service_type}\n'
    body += f'User Name: {user_name}\n'
    body += f'Apartment: {apartment}\n'
    body += f'Start Date: {StartDate}\n'
    body += f'Start Time: {start_time}\n'
    body += f'Special Requirements: {special_requirements}\n'
    body += f'Food Preferences: {food_preferences}\n'
    body += f'User Address: {user_address}\n'
    body += f'User Phone Number: {user_phone_number}\n'
    
    body += '\nThank you for choosing our services!'
    body +='\nThis is an auto generated mail. Please do not reply to this mail For any further queries feel free to contact us at support@yellowsense.in '

    
    # Send to the user and orders email
    recipients = [recipient, 'orders@yellowsense.in']
    msg = Message(subject, recipients=recipients, body=body)
    mail.send(msg)



@app.route('/signin', methods=['POST'])
@cross_origin()
def signin():
    try:
        # Extract parameters from the JSON body for POST requests
        data = request.json
        username = data.get('Username')
        mobile_number = data.get('MobileNumber')
        email = data.get('Email')
        password = data.get('Passwrd')
        role = data.get('Role')

        # Check if the user already exists based on mobile number and password
        cursor.execute(
            "SELECT * FROM accountdetails WHERE MobileNumber=? AND Passwrd=?",
            (mobile_number, password)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            # User already exists, return a message with status code 500
            return jsonify({"message": "User already registered. Please login."}), 500

        # User does not exist, proceed with registration
        cursor.execute(
            "INSERT INTO accountdetails (Username, MobileNumber, Email, Passwrd, Role) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, mobile_number, email, password, role)
        )
        conn.commit()

        # Return a success message with status code 200
        return jsonify({"message": "User registration successful"}), 200
    except Exception as e:
        app.logger.error(str(e))
        # Return an error message with status code 500
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/login', methods=['POST'])
@cross_origin()
def login():
    try:
        # Extract parameters from the JSON body for POST requests
        data = request.json
        mobile_number = data.get('MobileNumber')
        password = data.get('Passwrd')  # Assuming 'Passwrd' is the correct column name

        # Execute the SQL query to retrieve user details based on mobile number and password
        cursor.execute(
            "SELECT * FROM accountdetails WHERE MobileNumber=? AND Passwrd=?",
            (mobile_number, password)
        )
        row = cursor.fetchone()

        if row:
            # Return a success message with a 200 status code
            return jsonify({"message": "Login successful"}), 200
        else:
            # Return an error response with a 401 status code (Unauthorized)
            return jsonify({"message": "Invalid credentials"}), 401
    except pyodbc.Error as e:
        # Return an error response with a 500 status code (Internal Server Error)
        return jsonify({"error": str(e)}), 500

@app.route('/book_and_get_details', methods=['POST'])
@cross_origin()
def book_and_get_details():
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

        # Insert into BookingDetails and retrieve the last inserted ID
        cursor.execute('INSERT INTO BookingDetails (customer_mobile_number, provider_mobile_number) OUTPUT INSERTED.id VALUES (?, ?)', (customer_mobile_number, provider_mobile_number))
        last_inserted_id = cursor.fetchone().id
        conn.commit()

        query = '''
            SELECT
                bd.id AS booking_id,
                m.Id AS maid_id,
                m.Name AS maid_name,
                m.Gender AS maid_gender,
                m.Services AS maid_services,
                m.Locations AS maid_locations,
                ad.MobileNumber AS customer_mobile_number,
                ad.UserID AS customer_id,
                ad.Username AS customer_name,
                ad.Email AS customer_email
            FROM
                BookingDetails bd
                INNER JOIN maidreg m ON bd.provider_mobile_number = m.PhoneNumber
                INNER JOIN accountdetails ad ON bd.customer_mobile_number = ad.MobileNumber
            WHERE
                bd.id = ?
        '''

        cursor.execute(query, (last_inserted_id,))
        row = cursor.fetchone()

        if row:
            booking_details = {
                "booking_id": row.booking_id,
                "maid_details": {
                    "maid_id": row.maid_id,
                    "maid_name": row.maid_name,
                    "maid_gender": row.maid_gender,
                    "maid_services": row.maid_services.split(','),
                    "maid_locations": row.maid_locations.split(',')
                },
                "customer_details": {
                    "customer_id": row.customer_id,
                    "customer_mobile_number": row.customer_mobile_number,
                    "customer_name": row.customer_name,
                    "customer_email": row.customer_email
                }
            }

            return jsonify(booking_details)
        else:
            return jsonify({"error": "Booking not found"})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        cursor.close()

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

        # Update the related records in the "BookingDetails" table
        if new_mobile_number is not None:
            cursor.execute(
                "UPDATE BookingDetails SET customer_mobile_number = ? WHERE customer_mobile_number = ?",
                (new_mobile_number, user_mobile_number)
            )
            conn.commit()

        # Update the user profile based on the mobile number
        update_query = "UPDATE accountdetails SET"
        update_params = []

        if new_name is not None:
            update_query += " Username = ?,"
            update_params.append(new_name)

        if new_mobile_number is not None:
            update_query += " MobileNumber = ?,"
            update_params.append(new_mobile_number)

        if new_email is not None:
            update_query += " Email = ?,"
            update_params.append(new_email)

        # Remove the trailing comma if there are updates
        if update_params:
            update_query = update_query.rstrip(',')
            update_query += " WHERE MobileNumber = ?"
            update_params.append(user_mobile_number)

            cursor.execute(update_query, tuple(update_params))
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

def find_matching_service_providers(locations, services, start_time_str):

    try:
        cursor.execute("""
            SELECT ID, Name, Gender, Services, Locations, Timings
            FROM maidreg
            WHERE CHARINDEX(?, Locations) > 0
              AND CHARINDEX(?, Services) > 0
        """, (locations, services))

        rows = cursor.fetchall()

        start_time = parser.parse(f'1900-01-01 {start_time_str}').time()
        if start_time is None:
            app.logger.error("Invalid start_time format: %s", start_time_str)
            return {"error": "Invalid start_time format"}

        matching_providers = []
        for row in rows:
            row_services = [service.strip("' ") for service in row.Services.split(',')] if row.Services else []
            row_locations = [location.strip("' ") for location in row.Locations.split(',')] if row.Locations else []
            timings = [timing.strip("' ") for timing in row.Timings.split(',')] if row.Timings else []
            if isinstance(row_locations, list) and row_locations is not None:
                if any(locations.strip().lower() in loc.strip("' ").lower() for loc in row_locations):
                    if services.lower() in [serv.strip().lower() for serv in row_services]:
                        if isinstance(timings, list) and timings is not None:
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
                                        "Services": row_services,
                                        "Locations": row_locations,
                                        "Timings": timings
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
        services = request.args.get('Services')
        date = request.args.get('date')
        start_time = request.args.get('start_time')
    elif request.method == 'POST':
        data = request.json
        locations = data.get('Locations')
        services = data.get('Services')
        date = data.get('date')
        start_time = data.get('start_time')
    else:
        return jsonify({"error": "Unsupported method"})

    if not locations or not services or not date or not start_time:
        return jsonify({"error": "Missing parameters"})

    matching_providers = find_matching_service_providers(locations, services, start_time)

    if matching_providers:
        return jsonify({"providers": matching_providers})
    else:
        return jsonify({"providers": "No matching service providers found"})

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

        

        # Check if the user with the given mobile number exists
        cursor.execute('SELECT * FROM maidreg WHERE PhoneNumber = ?', (user_mobile_number,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Begin the transaction
        cursor.execute("BEGIN TRANSACTION;")

        # Update the related records in the "BookingDetails" table
        if new_mobile_number is not None:
            cursor.execute(
                "UPDATE BookingDetails SET provider_mobile_number = ? WHERE provider_mobile_number = ?",
                (new_mobile_number, user_mobile_number)
            )
            conn.commit()

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


        # Remove the trailing comma if there are updates
        if update_params:
            update_query = update_query.rstrip(',')
            update_query += " WHERE PhoneNumber = ?"
            update_params.append(user_mobile_number)

            cursor.execute(update_query, tuple(update_params))
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

@app.route('/get_customer_details', methods=['GET'])
@cross_origin()
def get_customer_details():
    try:
        # Extract the mobile number from the request parameters
        mobile_number = request.args.get('mobile_number')

        # Check if the mobile number is provided
        if not mobile_number:
            return jsonify({"error": "Missing mobile_number parameter"}), 400

        # Retrieve customer details based on mobile number from BookingDetails
        cursor.execute('SELECT * FROM BookingDetails WHERE customer_mobile_number = ?', (mobile_number,))
        booking_details = cursor.fetchone()

        if not booking_details:
            return jsonify({"error": "Customer not found in BookingDetails"}), 404

        # Retrieve additional details from AccountDetails using the mobile number
        cursor.execute('SELECT * FROM AccountDetails WHERE MobileNumber = ?', (mobile_number,))
        account_details = cursor.fetchone()

        if not account_details:
            return jsonify({"error": "Customer account details not found"}), 404

        # Combine both sets of details and return the response
        customer_details = {
            "booking_details": {
                "customer_mobile_number": booking_details.customer_mobile_number,
                "provider_mobile_number":booking_details.provider_mobile_number,
                "id":booking_details.id,
                # Add other booking details as needed
            },
            "account_details": {
                "Username": account_details.Username,
                "MobileNumber": account_details.MobileNumber,
                "Email": account_details.Email,
                # Add other account details as needed
            }
        }

        return jsonify(customer_details)
    except Exception as e:
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/get_customer/<string:mobile_number>', methods=['GET'])
@cross_origin()
def customer_details(mobile_number):
    try:

        # SQL query to retrieve customer details excluding the password
        query = f"SELECT UserID, Username, MobileNumber, Email FROM accountdetails WHERE MobileNumber = '{mobile_number}'"
        
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
                'Email': customer_details[3]
            }
            return jsonify(result)
        else:
            return jsonify({'message': 'Customer not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/serviceprovider/confirm', methods=['POST'])
@cross_origin()
def confirm_booking():
    data = request.get_json()

    provider_mobile = data.get('provider_mobile')
    action = data.get('action')

    # Execute raw SQL query to fetch the booking
    sql_query = f"SELECT TOP 1 * FROM BookingDetails WHERE provider_mobile_number = '{provider_mobile}' AND (status IS NULL OR status = 'pending');" 
    cursor.execute(sql_query)
    booking = cursor.fetchone()
    if booking:
        if action == 'accept':
            # Execute raw SQL query to update the booking status
            update_query = f"UPDATE BookingDetails SET status = 'accepted' WHERE id = {booking.id};"
            cursor.execute(update_query)
            provider_details_query = f"SELECT * FROM maidreg WHERE PhoneNumber = '{provider_mobile}';"
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
                        'timings': provider_details.Timings
                        }
                    }
                return jsonify(response)
            else:
                return jsonify({'message': 'Provider details not found'})
        elif action == 'reject':
            # Execute raw SQL query to update the booking status
            update_query = f"UPDATE BookingDetails SET status = 'rejected' WHERE id = {booking.id};"
            cursor.execute(update_query)
            conn.commit()
            return jsonify({'message': 'Booking rejected'})
    else:
        return jsonify({'message': 'Booking not found or already processed'})

@app.route('/customer-booking-details/<customer_mobile_number>', methods=['GET'])
@cross_origin()
def get_customer_booking_details(customer_mobile_number):
    # Query booking details for a specific customer
    booking_sql_query = f"SELECT * FROM BookingDetails WHERE customer_mobile_number = '{customer_mobile_number}'"
    cursor.execute(booking_sql_query)
    booking_details = cursor.fetchall()

    # Convert the query result to a list of dictionaries for JSON response
    booking_details_list = [dict(zip([column[0] for column in cursor.description], row)) for row in booking_details]

    if not booking_details_list:
        return jsonify({'message': 'No booking details found for the customer'}), 404

    # Get provider details for each booking using a separate SQL query
    provider_details_list = []
    for booking in booking_details_list:
        provider_mobile_number = booking['provider_mobile_number']
        provider_sql_query = f"SELECT * FROM MaidReg WHERE PhoneNumber = '{provider_mobile_number}'"
        cursor.execute(provider_sql_query)
        provider_details = cursor.fetchone()

        if provider_details:
            provider_details_dict = dict(zip([column[0] for column in cursor.description], provider_details))
            provider_details_dict[' booking id'] = booking['id']
            provider_details_list.append(provider_details_dict)

    return jsonify({ 'provider_details': provider_details_list})

def convert_date_format(date_str):
    try:
        # Try parsing as datemonthyear format
        return datetime.strptime(date_str, '%d%m%Y').strftime('%Y-%m-%d')
    except ValueError:
        try:
            # Try parsing as yearmonthdate format
            return datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
        except ValueError:
            try:
                # Try parsing as a different format (e.g., '07-12-2023')
                return datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y-%m-%d')
            except ValueError:
                # If all parsing attempts fail, raise an error or handle it as needed
                raise ValueError(f"Invalid date format: {date_str}")
            
def convert_time_to_string(time_obj, use_12_hour_format=True):
    if use_12_hour_format:
        return time_obj.strftime('%I:%M %p')
    else:
        return time_obj.strftime('%H:%M')

@app.route('/booknow', methods=['POST'])
@cross_origin()
def book_now():
    data = request.json

    customer_mobile_number = data.get('customer_mobile_number')
    provider_mobile_number = data.get('provider_mobile_number')

    # Fetch provider details from MaidReg based on the provided mobile number
    sql_query = f"SELECT * FROM maidreg WHERE PhoneNumber = '{provider_mobile_number}'"

    cursor.execute(sql_query)
    provider_details = cursor.fetchone()

    sql_query_customer = f"SELECT Username FROM accountdetails WHERE MobileNumber = '{customer_mobile_number}'"
    cursor.execute(sql_query_customer)
    customer_name_result = cursor.fetchone()

    if provider_details and customer_name_result:
        customer_name = customer_name_result.Username
        # Parse and format the date string
        date_str = data.get('date')
        formatted_date = convert_date_format(date_str)

        # Create a new booking entry
        new_booking = {
            'customer_mobile_number': customer_mobile_number,
            'provider_mobile_number': provider_mobile_number,
            'Location': data.get('Location'),
            'Services': data.get('Services'),
            'date': formatted_date,  # Use the formatted date
            'start_time': data.get('start_time'),
            'Customer_name': customer_name,
            'Provider_name': provider_details.Name,
            'Povider_locations': provider_details.Locations,
            'Provider_services': provider_details.Services
        }

        # Assuming you have a separate table for bookings or modify as needed
        booking_sql = f"INSERT INTO BookingDetails ({', '.join(new_booking.keys())}) OUTPUT INSERTED.id VALUES ({', '.join(['?' for _ in new_booking.values()])})"
        try:
            cursor.execute(booking_sql, list(new_booking.values()))
            last_inserted_id = cursor.fetchone().id
            app.logger.info(f"Inserted into BookingDetails. Last inserted ID: {last_inserted_id}")
            conn.commit()

            # Retrieve all details from BookingDetails for the last inserted ID
            cursor.execute(f"SELECT * FROM BookingDetails WHERE id = ?", (last_inserted_id,))
            booked_details = cursor.fetchone()

            # Convert time to string before serializing
            booked_details_date_str = booked_details.date.strftime('%Y-%m-%d')
            
            booked_details_start_time_str_12hr = convert_time_to_string(booked_details.start_time, use_12_hour_format=True)
            booked_details_start_time_str_24hr = convert_time_to_string(booked_details.start_time, use_12_hour_format=False)

            return jsonify({
                'message': 'Booking successful!',
                'last_inserted_id': last_inserted_id,
                'booked_details': {
                    'id': booked_details.id,
                    'customer_mobile_number': booked_details.customer_mobile_number,
                    'provider_mobile_number': booked_details.provider_mobile_number,
                    'Location': booked_details.Location,
                    'Services': booked_details.Services,
                    'date': booked_details_date_str,  # Convert time to string
                    # 'start_time': booked_details.start_time,
                    'start_time': booked_details_start_time_str_12hr,
                    # 'start_time_24hr': booked_details_start_time_str_24hr,
                    'Customer_name': booked_details.Customer_name,
                    'Provider_name': booked_details.Provider_name,
                    'Povider_locations': booked_details.Povider_locations,
                    'Provider_services': booked_details.Provider_services
                }
            }), 200
        except pyodbc.Error as e:
            app.logger.error("Error executing booking SQL query: %s", e)
            return jsonify({'message': 'Error creating booking'}), 500
        
    else:
        return jsonify({'message': 'Provider not found!'}), 404

@app.route('/update_account', methods=['PUT'])
@cross_origin()
def update_account():
    data = request.get_json()

    phone_number = data.get('phone_number')
    name = data.get('name')
    age = data.get('age')
    gender = data.get('gender')
    services = data.get('services')
    aadhar_number = data.get('aadhar_number')
    pan_card = data.get('pan_card')

    # Update the values in the accountdetails table
    account_query = "UPDATE accountdetails SET"
    if name is not None:
        account_query += f" Username='{name}',"
    if age is not None:
        account_query += f" Age={age},"
    if gender is not None:
        account_query += f" Gender='{gender}',"
    if services is not None:
        services = services.replace("'", "''")
        account_query += f" Services='{services}',"
    if aadhar_number is not None:
        account_query += f" AadharCard='{aadhar_number}',"
    if pan_card is not None:
        account_query += f" PanCardNumber='{pan_card}',"

    # Remove the trailing comma and complete the query
    account_query = account_query.rstrip(',') + f" WHERE MobileNumber ='{phone_number}'"

    # Update the values in the maidreg table
    maid_query = "UPDATE maidreg SET"
    if name is not None:
        maid_query += f" Name='{name}',"
    if age is not None:
        maid_query += f" age={age},"
    if gender is not None:
        maid_query += f" Gender='{gender}',"
    if services is not None:
        services = services.replace("'", "''")
        maid_query += f" Services='{services}',"
    if aadhar_number is not None:
        maid_query += f" AadharNumber='{aadhar_number}',"
    if pan_card is not None:
        maid_query += f" pancardnumber='{pan_card}',"

    # Remove the trailing comma and complete the query
    maid_query = maid_query.rstrip(',') + f" WHERE PhoneNumber='{phone_number}'"

    booking_query = "UPDATE BookingDetails SET"
    if name is not None:
        booking_query += f" Provider_name='{name}',"
    if services is not None:
        # Handle Services as a string, properly escaping single quotes
        services = services.replace("'", "''")
        booking_query += f" Services='{services}',"
            # Remove the trailing comma and complete the query
    booking_query = booking_query.rstrip(',') + f" WHERE provider_mobile_number='{phone_number}'"
    
    try:
        cursor.execute(account_query)
        cursor.execute(maid_query)
        conn.commit()
        return jsonify({'message': 'Profile data is  updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# #@app.route('/all-booking-details', methods=['GET'])
# #@cross_origin()
# #def get_all_booking_details():
#     # Query all booking details
#     booking_sql_query = "SELECT * FROM BookingDetails"
#     cursor.execute(booking_sql_query)
#     booking_details = cursor.fetchall()

#     # Convert the query result to a list of dictionaries for JSON response
#     booking_details_list = [dict(zip([column[0] for column in cursor.description], row)) for row in booking_details]

#     if not booking_details_list:
#         return jsonify({'message': 'No booking details found'}), 404

#     return jsonify({'booking_details': booking_details_list})


if __name__ == '__main__':
    app.run(debug=True)
