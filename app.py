from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import pyodbc
from datetime import time
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
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT'
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
        #Check if the specified location is in the provider's list of locations
        if isinstance(provider["Locations"], list) and provider["Locations"] is not None:
            # Update: Case-insensitive and whitespace-insensitive comparison
            if any(Locations.strip().lower() in loc.strip("' ").lower() for loc in provider["Locations"]):
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

@app.route('/get_all_booking_details', methods=['GET'])
@cross_origin()
def get_all_booking_details():
    try:
        cursor.execute("SELECT * FROM BookingDetails")
        rows = cursor.fetchall()

        columns = [column[0] for column in cursor.description]
        booking_details_list = [row_to_dict(row, columns) for row in rows]

        return jsonify({"booking_details": booking_details_list})
    except pyodbc.Error as e:
        app.logger.error("An error occurred: %s", str(e))
        return jsonify({"error": str(e)})
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

        # Update the user profile based on the mobile number
        cursor.execute(
            "UPDATE accountdetails SET Username = ?, MobileNumber = ?, Email = ? WHERE MobileNumber = ?",
            (new_name, new_mobile_number, new_email, user_mobile_number)
        )
        conn.commit()

        # Return a success message
        return jsonify({"message": "User profile updated successfully"})
    except Exception as e:
        # Log the error and return an error message in case of an exception
        app.logger.error(str(e))
        return jsonify({"error": "Internal Server Error"}), 500

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



if __name__ == '__main__':
    app.run(debug=True)
