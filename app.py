import flask
from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
import pyodbc
from datetime import time, timedelta, datetime
from dateutil import parser
from flask_mail import Mail, Message
from flask import make_response

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
@cross_origin(origin='https://www.yellowsense.in')
def get_society_names():
    try:
        # Execute a SQL query to retrieve society names and IDs
        cursor.execute("SELECT society_id, society_name FROM Society")
        rows = cursor.fetchall()

        # Convert the result into an array of dictionaries with id and name
        society_data = [{"id": row.society_id, "name": row.society_name} for row in rows]

        response=jsonify(society_data)  # Return JSON with id and name
        response.headers["Access-Control-Allow-Origin"]="https://yellowsense.in"
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
            return jsonify({"error": "User not found in maidreg table"}), 404

        # Begin the transaction
        cursor.execute("BEGIN TRANSACTION;")
        cursor.execute('SELECT * FROM accountdetails WHERE MobileNumber = ?', (user_mobile_number,))
        user_in_accountdetails = cursor.fetchone()
        print(f"user_in_accountdetails: {user_in_accountdetails}")

        cursor.execute("BEGIN TRANSACTION;")


        # Update the user profile based on the mobile number
        update_query = "UPDATE maidreg SET"
        update_params = []

        update_query_accountdetails = "UPDATE accountdetails SET"
        update_params_accountdetails = []


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

        if name is not None:
            update_query_accountdetails += " Username = ?,"
            update_params_accountdetails.append(data['name'])

        if new_mobile_number is not None:
            update_query_accountdetails += " MobileNumber = ?,"
            update_params_accountdetails.append(new_mobile_number)

        if aadhar_number is not None:
            update_query_accountdetails += " AadharCard = ?,"
            update_params_accountdetails.append(data['aadhar_number'])

        if pan_card is not None:
            update_query_accountdetails += " PanCardNumber = ?,"
            update_params_accountdetails.append(data['pan_card'])

        if age is not None:
            update_query_accountdetails += " Age = ?,"
            update_params_accountdetails.append(data['age'])

        if gender is not None:
            update_query_accountdetails += " Gender = ?,"
            update_params_accountdetails.append(data['gender'])

        if services is not None:
            update_query_accountdetails+= " Services = ?,"
            update_params_accountdetails.append(data['services'])

        

        # Remove the trailing comma if there are updates
        if update_params:
            update_query = update_query.rstrip(',')
            update_query += " WHERE PhoneNumber = ?"
            update_params.append(user_mobile_number)

            cursor.execute(update_query, tuple(update_params))
            conn.commit()
        if update_params_accountdetails:
            update_query_accountdetails = update_query_accountdetails.rstrip(',')
            update_query_accountdetails += " WHERE MobileNumber = ?"
            update_params_accountdetails.append(user_mobile_number)

            cursor.execute(update_query_accountdetails, tuple(update_params_accountdetails))
            conn.commit()

        cursor.execute(update_query_accountdetails, tuple(update_params_accountdetails))
        conn.commit()

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
        return jsonify({"error": "Duplicate phone number in maidreg or accountdetails table"}), 500
    except Exception as e:
        # Rollback the transaction in case of an exception
        cursor.execute("ROLLBACK TRANSACTION;")
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
    try:
        # Query booking details for a specific customer from ServiceBookings table
        booking_sql_query = f"SELECT * FROM ServiceBookings WHERE user_phone_number = '{customer_mobile_number}'"
        cursor.execute(booking_sql_query)
        booking_details = cursor.fetchall()

        # Convert the query result to a list of dictionaries for JSON response
        booking_details_list = [dict(zip([column[0] for column in cursor.description], row)) for row in booking_details]

        if not booking_details_list:
            return jsonify({'message': 'No booking details found for the customer'}), 404

        # Get provider details for each booking using a separate SQL query
        provider_details_list = []
        for booking in booking_details_list:
            provider_mobile_number = booking['provider_phone_number']
            provider_sql_query = f"SELECT * FROM MaidReg WHERE PhoneNumber = '{provider_mobile_number}'"
            cursor.execute(provider_sql_query)
            provider_details = cursor.fetchone()

            if provider_details:
                provider_details_dict = dict(zip([column[0] for column in cursor.description], provider_details))
                provider_details_dict['booking_id'] = booking['id']
                provider_details_list.append(provider_details_dict)

        return jsonify({'provider_details': provider_details_list})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


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

@app.route('/booknow', methods=['POST'])
@cross_origin()
def book_now():
    data = request.json

    customer_mobile_number = data.get('customer_mobile_number')
    provider_mobile_number = data.get('provider_mobile_number')

    # Fetch provider details from MaidReg based on the provided mobile number
    sql_query_provider = f"SELECT * FROM maidreg WHERE PhoneNumber = '{provider_mobile_number}'"
    cursor.execute(sql_query_provider)
    provider_details = cursor.fetchone()

    sql_query_customer = f"SELECT Username, Email FROM accountdetails WHERE MobileNumber = '{customer_mobile_number}'"
    cursor.execute(sql_query_customer)
    customer_details = cursor.fetchone()

    if provider_details and customer_details:

        # Parse and format the date string
        date_str = data.get('StartDate')
        formatted_date = convert_date_format(date_str)

        # Create a new booking entry
        new_booking = {
            'user_phone_number': customer_mobile_number,
            'provider_phone_number': provider_mobile_number,
            'service_type': data.get('service_type'),  # User-provided
            'apartment': data.get('apartment'),  # User-provided
            'StartDate': formatted_date,  # Use the formatted date
            'start_time': data.get('start_time'),  # User-provided
            'user_name': customer_details.Username,
            'user_email': customer_details.Email,
            'provider_name': provider_details.Name,
            'customer_status':data.get('status')  # Include provider details
        }

        # Check if the status is "Confirm" before storing in the database
        status = data.get('status')
        
        if status == 'Confirm':
            # Assuming you have a separate table for bookings or modify as needed
            booking_sql = f"INSERT INTO ServiceBookings ({', '.join(new_booking.keys())}) OUTPUT INSERTED.id VALUES ({', '.join(['?' for _ in new_booking.values()])})"
            try:
                cursor.execute(booking_sql, list(new_booking.values()))
                last_inserted_id = cursor.fetchone().id
                app.logger.info(f"Inserted into ServiceBookings. Last inserted ID: {last_inserted_id}")
                conn.commit()

                # Retrieve all details from ServiceBookings for the last inserted ID
                cursor.execute(f"SELECT * FROM ServiceBookings WHERE id = ?", (last_inserted_id,))
                booked_details = cursor.fetchone()

                # Convert time to string before serializing
                booked_details_date_str = booked_details.StartDate.strftime('%Y-%m-%d')
                booked_details_start_time_str_12hr = convert_time_to_string(booked_details.start_time, use_12_hour_format=True)

                return jsonify({
                    'message': 'Booking confirmed!',
                    'last_inserted_id': last_inserted_id,
                    'booked_details': {
                        'id': booked_details.id,
                        'user_phone_number': booked_details.user_phone_number,
                        'provider_phone_number': booked_details.provider_phone_number,
                        'service_type': booked_details.service_type,
                        'apartment': booked_details.apartment,
                        'StartDate': booked_details_date_str,
                        'start_time': booked_details_start_time_str_12hr,
                        'user_name': booked_details.user_name,
                        'user_email': booked_details.user_email,
                        'provider_name': booked_details.provider_name,
                    }
                }), 200
            except pyodbc.Error as e:
                app.logger.error("Error executing booking SQL query: %s", e)
                return jsonify({'message': 'Error confirming booking'}), 500
        elif status == 'Cancel':
            return jsonify({'message': 'Booking canceled!'}), 200
        else:
            return jsonify({'message': 'Invalid status provided!'}), 400
        
    else:
        return jsonify({'message': 'Provider or Customer not found!'}), 404

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

            # Insert into ServiceBookings and retrieve the last inserted ID
            cursor.execute('INSERT INTO ServiceBookings (user_phone_number, provider_phone_number, customer_status, user_name, provider_name) OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?)', (customer_mobile_number, provider_mobile_number, status, customer_username, provider_name))
            last_inserted_id = cursor.fetchone().id
            conn.commit()

            query = '''
                SELECT
                    sb.id AS booking_id,
                    sb.user_name,
                    sb.provider_name,
                    sb.provider_phone_number,
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
                    },
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
    data = request.args  # Use request.args for GET requests

    customer_mobile_number = data.get('customer_mobile_number')
    provider_mobile_number = data.get('provider_mobile_number')

    # Fetch provider details from MaidReg based on the provided mobile number
    sql_query_provider = f"SELECT ID, Name, PhoneNumber, Locations, Services FROM maidreg WHERE PhoneNumber = '{provider_mobile_number}'"
    cursor.execute(sql_query_provider)
    provider_details = cursor.fetchone()

    # Fetch customer details from AccountDetails based on the provided mobile number
    sql_query_customer = f"SELECT UserID, Username, MobileNumber FROM accountdetails WHERE MobileNumber = '{customer_mobile_number}'"
    cursor.execute(sql_query_customer)
    customer_details = cursor.fetchone()

    if provider_details and customer_details:
        # Your existing code for processing and returning the details

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
                'Services': provider_details.Services,
            }
        }), 200
    else:
        return jsonify({'message': 'Provider or Customer not found!'}),404

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
            update_query = f"UPDATE ServiceBookings SET status = 'accepted' WHERE id = {booking.id};"
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
                        'timings': provider_details.Timings
                    }
                }
                return jsonify(response)
            else:
                return jsonify({'message': 'Provider details not found'})
        elif action == 'reject':
            # Execute raw SQL query to update the booking status
            update_query = f"UPDATE ServiceBookings SET status = 'rejected' WHERE id = {booking.id};"
            cursor.execute(update_query)
            conn.commit()
            return jsonify({'message': 'Booking rejected'})
    else:
        return jsonify({'message': 'Booking not found or already processed'})

@app.route('/serviceprovider/ongoing_requests', methods=['GET'])
@cross_origin()
def ongoing_requests():
    provider_mobile = request.args.get('provider_mobile')

    # Execute raw SQL query to count ongoing (accepted) requests
    ongoing_query = f"SELECT COUNT(*) FROM ServiceBookings WHERE provider_phone_number = '{provider_mobile}' AND status = 'accepted';"
    cursor.execute(ongoing_query)
    ongoing_count = cursor.fetchone()[0]

    response = {
        'ongoing_requests': ongoing_count
    }

    return jsonify(response)

@app.route('/serviceprovider/cancelled_requests', methods=['GET'])
@cross_origin()
def cancelled_requests():
    provider_mobile = request.args.get('provider_mobile')

    # Execute raw SQL query to count canceled (rejected) requests
    cancelled_query = f"SELECT COUNT(*) FROM ServiceBookings WHERE provider_phone_number = '{provider_mobile}' AND status = 'rejected';"
    cursor.execute(cancelled_query)
    cancelled_count = cursor.fetchone()[0]

    response = {
        'cancelled_requests': cancelled_count
    }

    return jsonify(response)
@app.route('/customer/ongoing_requests', methods=['GET'])
@cross_origin()
def customer_ongoing_requests():
    customer_mobile = request.args.get('customer_mobile')

    # Execute raw SQL query to count ongoing (accepted) requests for the customer
    ongoing_query = f"SELECT COUNT(*) FROM ServiceBookings WHERE user_phone_number = '{customer_mobile}' AND status = 'accepted';"
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
    cancelled_query = f"SELECT COUNT(*) FROM ServiceBookings WHERE user_phone_number = '{customer_mobile}' AND status = 'rejected';"
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
        accepted_count = get_request_count(provider_mobile, 'accepted')
        rejected_count = get_request_count(provider_mobile, 'rejected')

        response = {
            'total_requests': total_count,
            'accepted_requests': accepted_count,
            'rejected_requests': rejected_count
        }
    elif request_type == 'total' or request_type == 'accepted' or request_type == 'rejected':
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
    elif request_type == 'accepted':
        status_condition = "status = 'accepted'"
    elif request_type == 'rejected':
        status_condition = "status = 'rejected'"
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

    if request_status not in ['accepted', 'rejected', 'total']:
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

        # Update or insert into accountdetails
        cursor.execute('SELECT * FROM accountdetails WHERE MobileNumber = ?', (user_mobile_number,))
        user_in_accountdetails = cursor.fetchone()

        if user_in_accountdetails:
            update_query_accountdetails = """
                UPDATE accountdetails
                SET Username = COALESCE(?, Username),
                    Services = COALESCE(?, Services),
                    Gender = COALESCE(?, Gender),
                    AadharCard = COALESCE(?, AadharCard),
                    PanCardNumber = COALESCE(?, PanCardNumber),
                    Age = COALESCE(?, Age),
                    Location = COALESCE(?, Location),
                    Languages = COALESCE(?, Languages)
                WHERE MobileNumber = ?
            """
            cursor.execute(
                update_query_accountdetails,
                (
                    data.get('name'),
                    data.get('services'),
                    data.get('gender'),
                    data.get('aadhar_number'),
                    data.get('pan_card'),
                    data.get('age'),
                    data.get('locations'),
                    data.get('languages'),
                    user_mobile_number
                )
            )
            conn.commit()
        else:
            insert_query_accountdetails = """
                INSERT INTO accountdetails (MobileNumber, Username, Services, Gender, AadharCard, PanCardNumber, Age, Location, Languages)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(
                insert_query_accountdetails,
                (
                    user_mobile_number,
                    data.get('name'),
                    data.get('services'),
                    data.get('gender'),
                    data.get('aadhar_number'),
                    data.get('pan_card'),
                    data.get('age'),
                    data.get('locations'),
                    data.get('languages')
                )
            )
            conn.commit()

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
            SELECT ID, Name, Gender, Services, Locations, Timings, RATING, Region
            FROM maidreg
            WHERE CHARINDEX(?, Services COLLATE SQL_Latin1_General_CP1_CI_AS) > 0
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
                                "Services": row_services,
                                "Locations": row_locations,
                                "Region": row_region,
                                "Timings": timings,
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
        return jsonify({"providers": "No matching service providers found"})

@app.route('/dynamic-greeting', methods=['GET'])
def dynamic_greeting():
    # Return plain text response
    greeting_text = "Hello, Happy New Year, and welcome to Yellowsense. You have received a booking for your service. Please press one to accept and two to reject."
    return Response(greeting_text, content_type='text/plain; charset=utf-8')

@app.route('/dynamic-greeting/maid', methods=['GET'])
def dynamic_greeting_maid():
    # Extract details from query parameters
    provider_name = request.args.get('provider_name')
    user_name = request.args.get('user_name')
    apartment = request.args.get('apartment')
    start_date = request.args.get('start_date')
    start_time = request.args.get('start_time')
    service_type = 'maid'  # Specific to maid service

    greeting_text = "Hi {provider_name},\n\nWelcome to Yellowsense! Someone called {user_name} from {apartment} apartment has booked for your {service_type} service to start work from {start_time} on {start_date}.\n"
    greeting_text += "Please confirm the booking by pressing one. To reject, press two."

    return Response(greeting_text.format(
        provider_name=provider_name,
        user_name=user_name,
        apartment=apartment,
        start_date=start_date,
        start_time=start_time,
        service_type=service_type
    ), content_type='text/plain; charset=utf-8')

@app.route('/dynamic-greeting/cook', methods=['GET'])
def dynamic_greeting_cook():
    # Extract details from query parameters
    provider_name = request.args.get('provider_name')
    user_name = request.args.get('user_name')
    apartment = request.args.get('apartment')
    start_date = request.args.get('start_date')
    start_time = request.args.get('start_time')
    service_type = 'cook'  # Specific to cook service

    greeting_text = "Hi {provider_name},\n\nWelcome to Yellowsense! Someone called {user_name} from {apartment} apartment has booked for your {service_type} service to start work from {start_time} on {start_date}.\n"
    greeting_text += "Please confirm the booking by pressing one. To reject, press two."

    return Response(greeting_text.format(
        provider_name=provider_name,
        user_name=user_name,
        apartment=apartment,
        start_date=start_date,
        start_time=start_time,
        service_type=service_type
    ), content_type='text/plain; charset=utf-8')

@app.route('/dynamic-greeting/nanny', methods=['GET'])
def dynamic_greeting_nanny():
    # Extract details from query parameters
    provider_name = request.args.get('provider_name')
    user_name = request.args.get('user_name')
    apartment = request.args.get('apartment')
    start_date = request.args.get('start_date')
    start_time = request.args.get('start_time')
    service_type = 'nanny'  # Specific to nanny service

    greeting_text = "Hi {provider_name},\n\nWelcome to Yellowsense! Someone called {user_name} from {apartment} apartment has booked for your {service_type} service to start work from {start_time} on {start_date}.\n"
    greeting_text += "Please confirm the booking by pressing one. To reject, press two."

    return Response(greeting_text.format(
        provider_name=provider_name,
        user_name=user_name,
        apartment=apartment,
        start_date=start_date,
        start_time=start_time,
        service_type=service_type
    ), content_type='text/plain; charset=utf-8')


if __name__ == '__main__':
    app.run(debug=True)
