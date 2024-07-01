import flask
from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
import pyodbc
from datetime import time, timedelta, datetime, date
from dateutil import parser
from flask_mail import Mail, Message
from flask import make_response
import requests
import json
import uuid
import logging 
import random

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://househelp.yellowsense.in", "https://yellowsense.in"]}})
app.config['CORS_HEADERS'] = 'Content-Type'
# CORS(app) 
#, resources={r"/*": {"origins": "*"}})
# app.config['CORS_HEADERS'] = 'Content-Type'

# Database connection setup
SERVER = 'serviceproviderdatasqlsever.database.windows.net'
DATABASE = 'Yellowsensesqldatabase'
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
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Your Azure Translator settings
translator_endpoint = "https://api.cognitive.microsofttranslator.com"
subscription_key = "fd061617ad6a42fb9c45ca3d7e11ffd1"
location = "centralindia"
custom_translations = {
    "Somu Sonnet": {
        "hi": "सोमु सोननेट",
        "te": "సోము సొన్నెట్",
        "kn": "ಸೋಮು ಸೊನೆಟ್"
    },
    "Sobha Eternia": {
        "hi": "शोभा एटरनिया",
        "te": "శోభా ఎటర్నియా",
        "kn": "ಶೋಭಾ ಎಟರ್ನಿಯಾ"
    },
    "Sattva Senorita": {
        "hi": "सत्वा सेनोरिटा",
        "te": "సత్వా సెనోరిటా",
        "kn": "ಸತ್ವ ಸೆನೊರಿಟಾ"
    },
    "VRR Fortuna": {
        "hi": "वीआरआर फॉर्चुना",
        "te": "విఆర్ ఆర్ ఫార్చునా",
        "kn": "ವಿಆರ್ ಆರ್ ಫಾರ್ಚುನಾ"
    },
    "UBER VERDANT": {
        "hi": "उबर वर्दांत",
        "te": "యూబర్ వెర్డాంట్",
        "kn": "ಯುಬರ್ ವರ್ಡಾಂಟ್"
    },
     "Assetz Here and Now": {
        "hi": "एसेट्स हियर एंड नाउ",
        "te": "అసెట్స్ హీర్ అండ్ నౌ",
        "kn": "ಆಸ್ಸೆಟ್ಸ್ ಹೀರ್ ಅಂಡ್ ನೌ"
    },
    "Regency Pinnacle Height (RPH)": {
        "hi": "रेजेंसी पिनाकल हाइट (आरपीएच)",
        "te": "రీజెన్సీ పినాకిల్ హైట్ (ఆర్పిహెచ్)",
        "kn": "ರೀಜೆನ್ಸಿ ಪಿನಾಕಲ್ ಹೆಯ್ಟ್ (ಆರ್‌ಪಿಹೆಚ್)"
    },
    "BTM Layout": {
        "hi": "बीटीएम लेआउट",
        "te": "బీటీఎం లేఅవుట్",
        "kn": "ಬಿಟಿಎಂ ಲೇಔಟ್"
    },
    "Doddenakundi": {
        "hi": "डोडेनाकुंडी",
        "te": "డోడెనాకుండి",
        "kn": "ಡೊಡೆನಕುಂಡಿ"
    },
    "Ect phase2": {
        "hi": "इक्ट फेज2",
        "te": "ఇక్ట్ ఫేజ్2",
        "kn": "ಇಕ್ಟ್ ಫೇಜ್2"
    },
    "Guddahatti": {
        "hi": "गुद्दहट्टी",
        "te": "గుద్దహట్టి",
        "kn": "ಗುದ್ದಹಟ್ಟಿ"
    },
    "HAL Layout": {
        "hi": "एचएल लेआउट",
        "te": "హెచ్‌ఎల్ లేఅవుట్",
        "kn": "ಹೆಚ್‌ಎಲ್ ಲೇಔಟ್"
    },
    "HBR Layout": {
        "hi": "एचबीआर लेआउट",
        "te": "హెచ్బిఆర్ లేఅవుట్",
        "kn": "ಹೆಚ್ಬಿಆರ್ ಲೇಔಟ್"
    },
    "Hongasandra": {
        "hi": "होंगासंद्रा",
        "te": "హొంగాసంద్ర",
        "kn": "ಹೊಂಗಾಸಂದ್ರ"
    },
    "Horamavu Agara": {
        "hi": "होरमावु आगरा",
        "te": "హొరమావు ఆగరా",
        "kn": "ಹೊರಮಾವು ಆಗರಾ"
    },
    "HSR Layout": {
        "hi": "एचएसआर लेआउट",
        "te": "హెచ్‌ఎస్‌ఆర్ లేఅవుట్",
        "kn": "ಹೆಚ್‌ಎಸ್‌ಆರ್ ಲೇಔಟ್"
    },
    "Mico Layout": {
        "hi": "माइको लेआउट",
        "te": "మైకో లేఅవుట్",
        "kn": "ಮೈಕೋ ಲೇಔಟ್"
    },
    "Munnekollal": {
        "hi": "मुन्नेकोल्लल",
        "te": "మున్నెకొల్లల్",
        "kn": "ಮುನ್ನೆಕೊಲ್ಲಲ್"
    },
    "Pai Layout": {
        "hi": "पाई लेआउट",
        "te": "పై లేఅవుట్",
        "kn": "ಪೈ ಲೇಔಟ್"
    },
    "RMV Extension": {
        "hi": "आरएमवी एक्सटेंशन",
        "te": "ఆర్ఎమ్వీ ఎక్స్టెన్షన్",
        "kn": "ಆರ್ಎಮ್ವೀ ಎಕ್ಸ್ಟೆನ್ಷನ್"
    },
    "Singasandra": {
        "hi": "सिंगासंद्रा",
        "te": "సింగాసంద్ర",
       "kn": "ಸಿಂಗಾಸಂದ್ರ"
    },
    "Tavarekere-BTM": {
        "hi": "तावारेकेरे-बीटीएम",
        "te": "తావారెకెరె-బీటీఎం",
        "kn": "ತಾವಾರೆಕೆರೆ-ಬಿಟಿಎಂ"
    },
    "Thindlu": {
        "hi": "थिंदलू",
        "te": "థింద్లు",
        "kn": "ಥಿಂದ್ಲು"
    },
    "Varthur": {
        "hi": "वर्थुर",
        "te": "వర్థుర్",
        "kn": "ವರ್ಥುರ್"
    },
    "Adugodi": {
        "hi": "आदुगोडि",
        "te": "అడుగోడి",
        "kn": "ಅಡುಗೋಡಿ"
    },
    "Attibele": {
        "hi": "अत्तिबेले",
        "te": "అట్టిబెలె",
        "kn": "ಅಟ್ಟಿಬೆಲೆ"
    },
    "Kogilu": {
        "hi": "कोगिलु",
        "te": "కొగిలు",
        "kn": "ಕೊಗಿಲು"
    },
    "Kudlu Gate": {
        "hi": "कुडलु गेट",
        "te": "కుడ్లు గేట్",
        "kn": "ಕುಡ್ಲು ಗೇಟ್"
    },
    "Jakkuru Layout": {
        "hi": "जाक्कुरु लेआउट",
        "te": "జాక్కురు లేఅవుట్",
        "kn": "ಜಾಕ್ಕುರು ಲೇಔಟ್"
    },
    "Chelekare": {
        "hi": "चेलेकरे",
        "te": "చెలెకరే",
        "kn": "ಚೆಲೆಕರೇ"
    }
}

# Function to translate text using Azure Translator
def translate_text(text, target_language):
    if text in custom_translations and target_language in custom_translations[text]:
        return custom_translations[text][target_language]

    path = '/translate?api-version=3.0'
    constructed_url = translator_endpoint + path

    params = {
        'from': 'en',
        'to': target_language
    }

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{'text': text}]

    try:
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status()
        translations = response.json()
        translated_text = translations[0]['translations'][0]['text']
        translated_text = ' '.join(translated_text.split())
        print(f"Original: {text} -> Translated: {translated_text}")  # Debugging output
        return translated_text
    except requests.exceptions.RequestException as e:
        print(f"Translation request failed for text '{text}': {e}")
        return text  # Return original text on translation failure

    

@app.route('/society_names', methods=['GET'])
@cross_origin()
def get_society_names():
    try:
        # Execute a SQL query to retrieve society names and IDs
        cursor.execute("SELECT society_id, society_name, SocietyCode FROM Society")
        rows = cursor.fetchall()

        # Get the language parameter from the query string, defaulting to English ('en')
        target_language = request.args.get('language', 'en')

        # Prepare the response data
        society_data = []

        # Translate society names if the target language is not English
        for row in rows:
            society_name = row.society_name
            if target_language != 'en':
                society_name = translate_text(society_name, target_language)
            society_data.append({
                "id": row.society_id,
                "name": society_name,
                "code": row.SocietyCode
            })

        response = jsonify(society_data)
        return response
    except pyodbc.Error as e:
        return jsonify({"error": str(e)})


@app.route('/area_names', methods=['GET'])
@cross_origin()
def get_area_names():
    try:
        # Get the language parameter from the query string, defaulting to English ('en')
        language = request.args.get('language', 'en')

        # Execute a SQL query to retrieve area IDs and names
        cursor.execute("SELECT AreaID, AreaName FROM Area")
        rows = cursor.fetchall()

        # Prepare the response data
        area_data = []

        # Translate area names if the target language is not English
        for row in rows:
            area_name = row.AreaName
            if language != 'en':
                area_name = translate_text(row.AreaName, language)
            area_data.append({
                "id": row.AreaID,
                "name": area_name
            })

        return jsonify(area_data)  # Return JSON with id and translated name
    
    except pyodbc.Error as e:
        error_message = {"error": str(e)}
        logging.error(f"Database query error: {error_message}")
        return jsonify(error_message), 500  # Return error response with HTTP status code 500

    except Exception as e:
        error_message = {"error": str(e)}
        logging.error(f"An unexpected error occurred: {error_message}")
        return jsonify(error_message), 500  # Return error response with HTTP status code 500
    
        
# @app.route('/society_names', methods=['OPTIONS', 'GET', 'POST', 'HEAD'])
# @cross_origin()
# def get_society_names():
#     try:
#         # Execute a SQL query to retrieve society names and IDs
#         cursor.execute("SELECT society_id, society_name FROM Society")
#         rows = cursor.fetchall()

#         # Convert the result into an array of dictionaries with id and name
#         society_data = [{"id": row.society_id, "name": row.society_name} for row in rows]

#         response=jsonify(society_data)  # Return JSON with id and name
        
#         # Set CORS headers
#         # response.headers["Access-Control-Allow-Origin"]="https://yellowsense.in/"
#         response.headers['Access-Control-Allow-Origin'] = '*'
#         response.headers["Access-Control-Allow-Methods"]= "GET, POST, OPTIONS, HEAD"
#         response.headers["Access-Control-Allow-Headers"]= "Content-Type"
#         return response
#     except pyodbc.Error as e:
#         return jsonify({"error": str(e)})
        
# @app.route('/insert_maid', methods=['POST'])
# @cross_origin()
# def insert_maid():
#     try:
#         # Extract parameters from the JSON body for POST requests
#         data = request.json
#         aadhar_number = data.get('AadharNumber')
#         name = data.get('Name')
#         phone_number = data.get('PhoneNumber')
#         gender = data.get('Gender')
#         services = data.get('Services')
#         locations = data.get('Locations')
#         timings = data.get('Timings')
#         age = data.get('age')
#         languages = data.get('languages')
#         Region = data.get('Region')

#         # Check if the phone number already exists in the database
#         cursor = conn.cursor()
#         cursor.execute("SELECT COUNT(*) FROM maidreg WHERE PhoneNumber = ?", (phone_number,))
#         count = cursor.fetchone()[0]

#         if count > 0:
#             # Phone number already registered, return a message
#             return jsonify({"error": "Phone number already registered"}), 400

#         # Execute the stored procedure
#         cursor.execute(
#             "EXEC InsertMaidRegistration "
#             "@AadharNumber = ?, "
#             "@Name = ?, "
#             "@PhoneNumber = ?, "
#             "@Gender = ?, "
#             "@Services = ?, "
#             "@Locations = ?, "
#             "@Timings = ?,"
#             "@age = ?, "
#             "@languages = ?, "
#             "@Region = ? ",
#             (aadhar_number, name, phone_number, gender, services, locations, timings, age, languages, Region)
#         )
#         conn.commit()
#         cursor.close()

#         # Return a success message
#         return jsonify({"message": "Maid entry added successfully"})
#     except Exception as e:
#         # Log the error and return an error message in case of an exception
#         app.logger.error(str(e))
#         return jsonify({"error": "Internal Server Error"}), 500

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
        age = data.get('age')  # Age is optional
        languages = data.get('languages')
        region = data.get('Region')  # Region is optional

        # Convert phone_number and aadhar_number to strings
        if phone_number is not None:
            phone_number = str(phone_number)
        if aadhar_number is not None:
            aadhar_number = str(aadhar_number)

        # Default status value
        status = "available"

        # Check if the phone number already exists in the database
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM maidreg WHERE PhoneNumber = ?", (phone_number,))
        count = cursor.fetchone()[0]

        if count > 0:
            # Phone number already registered, return a message
            return jsonify({"error": "Phone number already registered"}), 400

        # Build the SQL query
        sql_query = "INSERT INTO maidreg (AadharNumber, Name, PhoneNumber, Gender, Services, Timings, languages, status"
        sql_values = "VALUES (?, ?, ?, ?, ?, ?, ?, ?"
        params = [aadhar_number, name, phone_number, gender, services, timings, languages, status]

        if age is not None:
            sql_query += ", age"
            sql_values += ", ?"
            params.append(age)

        if locations is not None:
            sql_query += ", Locations"
            sql_values += ", ?"
            params.append(locations)

        if region is not None:
            sql_query += ", Region"
            sql_values += ", ?"
            params.append(region)

        sql_query += ") " + sql_values + ")"

        # Execute the SQL query to insert maid's information
        cursor.execute(sql_query, tuple(params))

        # Commit the transaction
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

# @app.route('/signup', methods=['POST'])
# @cross_origin()
# def signup():
#     try:
#         # Extract parameters from the JSON body for POST requests
#         data = request.json
#         username = data.get('Username')
#         mobile_number = data.get('MobileNumber')
#         role = data.get('Role')

#         if role == 'Customer':
#             # Check if the mobile number is already present in accountdetails
#             cursor.execute("SELECT * FROM accountdetails WHERE MobileNumber=?", (mobile_number,))
#             existing_user = cursor.fetchone()

#             if existing_user:
#                 # User already exists, return a message with status code 409 (Conflict)
#                 return jsonify({"error": "User already registered. Please login."}), 409

#             # Insert values into accountdetails table
#             cursor.execute(
#                 "INSERT INTO accountdetails (Username, MobileNumber, Role) "
#                 "VALUES (?, ?, ?)",
#                 (username, mobile_number, role)
#             )
#         else:
#             # Check if the mobile number is already present in maidreg
#             cursor.execute("SELECT * FROM maidreg WHERE PhoneNumber=?", (mobile_number,))
#             existing_maid = cursor.fetchone()

#             if existing_maid:
#                 # User already exists, return a message with status code 409 (Conflict)
#                 return jsonify({"error": "User already registered as a Servicer. Please login."}), 409

#             # Insert values into maidreg table
#             cursor.execute(
#                 "INSERT INTO maidreg (Name, PhoneNumber) "
#                 "VALUES (?, ?)",
#                 (username, mobile_number)
#             )

#         conn.commit()

#         # Return a success message with status code 200
#         return jsonify({"message": "User registration successful"}), 200

#     except pyodbc.Error as e:
#         app.logger.error(str(e))
#         # Return an error message with status code 500
#         return jsonify({"error": "Internal Server Error"}), 500

def generate_unique_code():
    while True:
        unique_code = f"{random.randint(1000, 9999):04d}"  # Format to 4-digit string
        cursor.execute("SELECT * FROM accountdetails WHERE unique_code=?", (unique_code,))
        if not cursor.fetchone():
            return unique_code

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

            # Generate a unique 4-digit code
            unique_code = generate_unique_code()

            # Insert values into accountdetails table
            cursor.execute(
                "INSERT INTO accountdetails (Username, MobileNumber, Role, unique_code) "
                "VALUES (?, ?, ?, ?)",
                (username, mobile_number, role, unique_code)
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
                'Email': customer_details[3],
            }
            return jsonify(result)
        else:
            return jsonify({'message': 'Customer not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# @app.route('/customer-booking-details/<customer_mobile_number>', methods=['GET'])
# @cross_origin()
# def get_customer_booking_details(customer_mobile_number):
#     try:
#         # Query booking details for a specific customer from ServiceBookings table
#         booking_sql_query = f"SELECT * FROM ServiceBookings WHERE user_phone_number = '{customer_mobile_number}' ORDER BY id DESC"
#         cursor.execute(booking_sql_query)
#         booking_details = cursor.fetchall()

#         # Convert the query result to a list of dictionaries for JSON response
#         booking_details_list = [dict(zip([column[0] for column in cursor.description], row)) for row in booking_details]

#         if not booking_details_list:
#             return jsonify({'message': 'No booking details found for the customer'}), 404

#         # Process booking details to create provider details list
#         provider_details_list = []
#         for booking in booking_details_list:
#             provider_details_dict = {
#                 'provider_name': booking['provider_name'],
#                 'service_type': booking['service_type'],
#                 'status': booking['status'],
#                 'ServiceStatus' : booking['ServiceStatus'],
#                 'booking_id': booking['id'],
#                 'StartDate': booking['StartDate'],
#                 'start_time': booking['start_time'],
#                 'user_address': booking['user_address'],
#                 'TotalAmount': booking['TotalAmount']
#             }

#             # If apartment is empty, use Region as the location key
#             if not booking['apartment']:
#                 provider_details_dict['location'] = booking['Region']
#             else:
#                 # If apartment has a value, use it as the location key
#                 provider_details_dict['location'] = booking['apartment']

#             provider_details_list.append(provider_details_dict)

#         return jsonify({'provider_details': provider_details_list})

#     except Exception as e:
#         print(f"Error: {str(e)}")
#         return jsonify({"error": "Internal Server Error"}), 500

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

        # Fetch all details from the maidreg table
        maidreg_sql_query = "SELECT Name, PhoneNumber, Gender, Age, Languages, Timings, Services, Locations, Region, RATING, Years_of_Experience, image FROM maidreg"
        cursor.execute(maidreg_sql_query)
        maid_details_all = cursor.fetchall()

        # Convert maid details to a list of dictionaries
        maid_details_list = [dict(zip([column[0] for column in cursor.description], row)) for row in maid_details_all]

        # Process booking details to create provider details list
        provider_details_list = []
        for booking in booking_details_list:
            provider_details_dict = {
                'ServiceStatus': booking['ServiceStatus'],
                'StartDate': booking['StartDate'],
                'TotalAmount': booking['TotalAmount'],
                'booking_id': booking['id'],
                'location': booking['Region'] if not booking['apartment'] else booking['apartment'],
                'provider_name': booking['provider_name'],
                'provider_phone_number': booking['provider_phone_number'],
                'service_type': booking['service_type'],
                'start_time': booking['start_time'],
                'status': booking['status'],
                'user_address': booking['user_address'],
                'WorkersAmount': booking['worksAmount'],
                'YellowsenseCommission': booking['ysComAmount'],
                'AmountPaid': booking['TransactionAmount']
            }

            # Find the maid details corresponding to the provider_phone_number
            maid_details = next((maid for maid in maid_details_list if maid['PhoneNumber'] == booking['provider_phone_number']), None)

            # If maid details are not found, set maid details as empty dictionary
            if maid_details is None:
                maid_details = {}

            # Count completed services for the current provider_phone_number directly from the database
            completed_services_query = f"SELECT COUNT(*) FROM ServiceBookings WHERE provider_phone_number = '{booking['provider_phone_number']}' AND ServiceStatus = 'Completed'"
            cursor.execute(completed_services_query)
            completed_services_count = cursor.fetchone()[0]

            # Update maid details with completed services count
            maid_details.update({'Completed_Services': completed_services_count})

            provider_details_dict.update({'maid_details': maid_details})  # Append maid details to provider details

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

            # Additional fields
            custom_services = data.get('CustomServices', '')  # default to empty string if not provided
            booking_type = data.get('BookingType', '')  # default to empty string if not provided
            preferred_gender = data.get('PreferredGender', '')  # default to empty string if not provided
            cooking_options = data.get('CookingOptions', '')  # default to empty string if not provided
            age_of_children = data.get('AgeOfChildren', '')  # default to empty string if not provided
            specific_preference = data.get('SpecificPreference', '')  # default to empty string if not provided

            # Determine the status and ServiceStatus based on the status provided
            if status == 'cancel':
                booking_status = 'cancel'
                service_status = 'canceled'
            elif status == 'confirm':
                booking_status = 'Pending'
                service_status = ''
            else:
                return jsonify({"error": "Invalid customer status"}), 400

            # Insert into ServiceBookings table
            cursor.execute('''
                INSERT INTO ServiceBookings (
                    user_phone_number, provider_phone_number, customer_status, user_name, 
                    provider_name, start_time, StartDate, service_type, apartment, 
                    Region, user_address, Status, ServiceStatus,
                    CustomServices, BookingType, PreferredGender, CookingOptions, AgeOfChildren, SpecificPreference
                ) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (customer_mobile_number, provider_mobile_number, status, customer_username, 
                provider_name, start_time, start_date, service, apartment, area, user_address,
                booking_status, service_status, custom_services, booking_type, preferred_gender,
                cooking_options, age_of_children, specific_preference)
            )
            conn.commit()

            # Retrieve the last inserted ID
            cursor.execute('SELECT MAX(id) FROM ServiceBookings')
            last_inserted_id = cursor.fetchone()[0]

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
                    sb.customer_status,
                    sb.CustomServices,
                    sb.BookingType,
                    sb.PreferredGender,
                    sb.CookingOptions,
                    sb.AgeOfChildren,
                    sb.SpecificPreference
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
                    "customer_status": row.customer_status,
                    "CustomServices": row.CustomServices,
                    "BookingType": row.BookingType,
                    "PreferredGender": row.PreferredGender,
                    "CookingOptions": row.CookingOptions,
                    "AgeOfChildren": row.AgeOfChildren,
                    "SpecificPreference": row.SpecificPreference
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

# @app.route('/profile_details', methods=['POST'])
# @cross_origin()
# def profile_details():
#     try:
#         data = request.json
#         user_mobile_number = data.get('user_mobile_number')

#         cursor.execute("BEGIN TRANSACTION;")

#         # Update or insert into maidreg
#         cursor.execute('SELECT * FROM maidreg WHERE PhoneNumber = ?', (user_mobile_number,))
#         user_in_maidreg = cursor.fetchone()

#         if user_in_maidreg:
#             update_query_maidreg = """
#                 UPDATE maidreg
#                 SET Name = COALESCE(?, Name),
#                     Services = COALESCE(?, Services),
#                     Locations = COALESCE(?, Locations),
#                     Timings = COALESCE(?, Timings),
#                     AadharNumber = COALESCE(?, AadharNumber),
#                     RATING = COALESCE(?, RATING),
#                     languages = COALESCE(?, languages),
#                     second_category = COALESCE(?, second_category),
#                     Region = COALESCE(?, Region),
#                     description = COALESCE(?, description),
#                     Sunday_availability = COALESCE(?, Sunday_availability),
#                     years_of_experience = COALESCE(?, years_of_experience),
#                     age = COALESCE(?, age),
#                     Gender = COALESCE(?, Gender),
#                     pancardnumber = COALESCE(?, pancardnumber)
#                 WHERE PhoneNumber = ?
#             """
#             cursor.execute(
#                 update_query_maidreg,
#                 (
#                     data.get('name'),
#                     data.get('services'),
#                     data.get('locations'),
#                     data.get('timings'),
#                     data.get('aadhar_number'),
#                     data.get('rating'),
#                     data.get('languages'),
#                     data.get('second_category'),
#                     data.get('region'),
#                     data.get('description'),
#                     data.get('sunday_availability'),
#                     data.get('years_of_experience'),
#                     data.get('age'),
#                     data.get('gender'),
#                     data.get('pan_card'),
#                     user_mobile_number,
#                 )
#             )
#             conn.commit()
#         else:
#             insert_query_maidreg = """
#                 INSERT INTO maidreg (PhoneNumber, Name, Services, Locations, Timings, AadharNumber , RATING ,languages, second_category , Region , description , Sunday_availability ,years_of_experience, age , Gender , pancardnumber)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             """
#             cursor.execute(
#                 insert_query_maidreg,
#                 (
#                     user_mobile_number,
#                     data.get('name'),
#                     data.get('services'),
#                     data.get('locations'),
#                     data.get('timings'),
#                     data.get('aadhar_number'),
#                     data.get('rating'),
#                     data.get('languages'),
#                     data.get('second_category'),
#                     data.get('region'),
#                     data.get('description'),
#                     data.get('sunday_availability'),
#                     data.get('years_of_experience'),
#                     data.get('age'),
#                     data.get('gender'),
#                     data.get('pan_card'),
#                 )
#             )
#             conn.commit()

#         cursor.execute("COMMIT TRANSACTION;")

#         return jsonify({"message": "User profile updated or created successfully"})
#     except pyodbc.IntegrityError as e:
#         cursor.execute("ROLLBACK TRANSACTION;")
#         app.logger.error(str(e))
#         return jsonify({"error": "Duplicate phone number in maidreg or accountdetails table"}), 500
#     except Exception as e:
#         cursor.execute("ROLLBACK TRANSACTION;")
#         app.logger.error(str(e))
#         return jsonify({"error": "Internal Server Error"}), 500

def translate_to_english(text):
    if not text:
        return text

    path = '/translate?api-version=3.0'
    constructed_url = translator_endpoint + path

    params = {
        'to': 'en'  # Target language is English
    }

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{'text': text}]

    try:
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status()
        translations = response.json()
        return translations[0]['translations'][0]['text']
    except requests.exceptions.RequestException as e:
        app.logger.error("Translation request failed: %s", e)
        return text  # Return original text on translation failure

@app.route('/profile_details', methods=['POST'])
@cross_origin()
def profile_details():
    try:
        data = request.json
        user_mobile_number = data.get('user_mobile_number')

        name = translate_to_english(data.get('name'))
        services = translate_to_english(data.get('services'))
        locations = translate_to_english(data.get('locations'))
        timings = data.get('timings')
        aadhar_number = translate_to_english(data.get('aadhar_number'))
        rating = translate_to_english(data.get('rating'))
        languages = data.get('languages')
        second_category = translate_to_english(data.get('second_category'))
        region = translate_to_english(data.get('region'))
        description = translate_to_english(data.get('description'))
        sunday_availability = translate_to_english(data.get('sunday_availability'))
        years_of_experience = translate_to_english(data.get('years_of_experience'))
        age = translate_to_english(data.get('age'))
        gender = translate_to_english(data.get('gender'))
        pan_card = translate_to_english(data.get('pan_card'))

        cursor = conn.cursor()
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
                    name,
                    services,
                    locations,
                    timings,
                    aadhar_number,
                    rating,
                    languages,
                    second_category,
                    region,
                    description,
                    sunday_availability,
                    years_of_experience,
                    age,
                    gender,
                    pan_card,
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
                    name,
                    services,
                    locations,
                    timings,
                    aadhar_number,
                    rating,
                    languages,
                    second_category,
                    region,
                    description,
                    sunday_availability,
                    years_of_experience,
                    age,
                    gender,
                    pan_card,
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

# # Flask route to retrieve area names with optional language parameter
# @app.route('/area_names', methods=['GET'])
# @cross_origin()
# def get_area_names():
#     language = request.args.get('language', 'en')  # Default to English if language parameter not provided
    
#     try:
#         # Execute a SQL query to retrieve area IDs and names
#         cursor.execute("SELECT AreaID, AreaName FROM Area")
#         rows = cursor.fetchall()

#         # Convert the result into an array of dictionaries with id and name
#         area_data = [{"id": row.AreaID, "name": translate_text(row.AreaName, language)} for row in rows]

#         return jsonify(area_data)  # Return JSON with id and translated name
    
#     except pyodbc.Error as e:
#         error_message = {"error": str(e)}
#         logging.error(f"Database query error: {error_message}")
#         return jsonify(error_message), 500  # Return error response with HTTP status code 500

#     except Exception as e:
#         error_message = {"error": str(e)}
#         logging.error(f"An unexpected error occurred: {error_message}")
#         return jsonify(error_message), 500  # Return error response with HTTP status code 500

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
def find_matching_service_providers(locations, services, start_time_str, region, gender=None):
    try:
        # Check if services is empty
        if not services:
            return {"error": "'services' is mandatory"}

        # Initial part of the query
        query = """
            SELECT ID, Name, Gender, Services, Locations, PhoneNumber, Timings, RATING, Region, Image
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

        # Check if gender is provided
        if gender:
            query += " AND Gender = ?"

        # Order by rating
        query += " ORDER BY RATING DESC"

        params = [services]

        if locations:
            params.append(locations)
        if region is not None:
            params.append(region)
        if gender:
            params.append(gender)

        cursor.execute(query, tuple(params))
        
        rows = cursor.fetchall()

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

            # Check if gender is provided and match with row's gender
            if gender and row.Gender.lower() != gender.lower():
                continue

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
                                "PhoneNumber": row.PhoneNumber,
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
        gender = request.args.get('Gender')  # Add gender parameter
    elif request.method == 'POST':
        data = request.json
        locations = data.get('Locations')
        region = data.get('Region')
        services = data.get('Services')
        date = data.get('date')
        start_time = data.get('start_time')
        gender = data.get('Gender')  # Add gender parameter
    else:
        return jsonify({"error": "Unsupported method"})
    
    if locations is None and region is None and not services or not date or not start_time:
        return jsonify({"error": "Either 'locations' or 'region' is mandatory"})

    matching_providers = find_matching_service_providers(locations, services, start_time, region, gender)  # Pass gender parameter

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

# @app.route('/get_latest_details', methods=['GET'])
# @cross_origin()
# def get_latest_details():
#     try:
#         mobile_number = request.args.get('mobile_number')

#         print(f"Received request for mobile_number: {mobile_number}")

#         cursor = conn.cursor()

#         # Query to retrieve the latest 5 details for the specified mobile number
#         query = (
#             "SELECT TOP 5 user_name, service_type, apartment, StartDate, start_time, status "
#             "FROM ServiceBookings "
#             "WHERE provider_phone_number = ? "
#             "ORDER BY created_at DESC;"
#         )

#         cursor.execute(query, mobile_number)
#         latest_details = cursor.fetchall()

#         if latest_details:
#             # Convert the pyodbc.Row objects to a list of dictionaries
#             result = []
#             for details in latest_details:
#                 details_dict = dict(zip([column[0] for column in cursor.description], details))
#                 # Format the StartDate field using strftime
#                 details_dict['StartDate'] = details_dict['StartDate'].strftime('%Y-%m-%d')  # Adjust the format as needed
#                 result.append(details_dict)

#             print(f"Latest details for mobile_number {mobile_number}: {result}")
#             return jsonify({'latest_details': result})
#         else:
#             # If there are no latest details, retrieve all details (up to 5)
#             all_details_query = (
#                 "SELECT user_name, service_type, apartment, StartDate, start_time, status "
#                 "FROM ServiceBookings "
#                 "WHERE provider_phone_number = ? "
#                 "ORDER BY created_at DESC;"
#             )

#             cursor.execute(all_details_query, mobile_number)
#             all_details = cursor.fetchall()

#             if all_details:
#                 # Convert the pyodbc.Row objects to a list of dictionaries
#                 result = []
#                 for details in all_details:
#                     details_dict = dict(zip([column[0] for column in cursor.description], details))
#                     # Format the StartDate field using strftime
#                     details_dict['StartDate'] = details_dict['StartDate'].strftime('%Y-%m-%d')  # Adjust the format as needed
#                     result.append(details_dict)

#                 print(f"All available details for mobile_number {mobile_number}: {result}")
#                 return jsonify({'latest_details': result})
#             else:
#                 print(f"No details found for mobile_number {mobile_number}")
#                 return jsonify({'error': 'No details found for the provided mobile number'}), 404

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

@app.route('/get_latest_details', methods=['GET'])
@cross_origin()
def get_latest_details():
    try:
        mobile_number = request.args.get('mobile_number')
        target_language = request.args.get('language', 'en')  # Default to English if not provided

        print(f"Received request for mobile_number: {mobile_number}")

        cursor = conn.cursor()

        # Query to retrieve details for the specified mobile number
        query = (
            "SELECT user_name, service_type, apartment, StartDate, start_time, status "
            "FROM ServiceBookings "
            "WHERE provider_phone_number = ? "
            "ORDER BY created_at DESC;"
        )

        cursor.execute(query, mobile_number)
        details = cursor.fetchall()

        if not details:
            print(f"No details found for mobile_number {mobile_number}")
            return jsonify({'error': 'No details found for the provided mobile number'}), 404

        result = []
        for detail in details:
            details_dict = dict(zip([column[0] for column in cursor.description], detail))
            details_dict['StartDate'] = details_dict['StartDate'].strftime('%Y-%m-%d')  # Adjust the format as needed
            
            # Translate each field
            for key in details_dict:
                if details_dict[key]:
                    details_dict[key] = translate_text(details_dict[key], target_language)
            
            result.append(details_dict)

        print(f"Latest details for mobile_number {mobile_number}: {result}")

        # Fetch accepted/rejected requests
        acceptance_query = (
            "SELECT booking_id, status "
            "FROM AcceptanceDetails "
            "WHERE provider_number = ?;"
        )

        cursor.execute(acceptance_query, mobile_number)
        acceptance_details = cursor.fetchall()

        if acceptance_details:
            accepted_rejected_results = []
            for acceptance in acceptance_details:
                booking_id, status = acceptance

                # Fetch details from ServiceBookings table based on booking_id
                booking_query = (
                    "SELECT user_name, service_type, apartment, StartDate, start_time, status "
                    "FROM ServiceBookings "
                    "WHERE id = ?;"
                )

                cursor.execute(booking_query, booking_id)
                booking_details = cursor.fetchone()

                if booking_details:
                    booking_details_dict = dict(zip([column[0] for column in cursor.description], booking_details))
                    booking_details_dict['StartDate'] = booking_details_dict['StartDate'].strftime('%Y-%m-%d')  # Adjust the format as needed
                    
                    # Translate each field
                    for key in booking_details_dict:
                        if booking_details_dict[key]:
                            booking_details_dict[key] = translate_text(booking_details_dict[key], target_language)
                    
                    booking_details_dict['status'] = status  # Add the status from AcceptanceDetails
                    accepted_rejected_results.append(booking_details_dict)

            result.extend(accepted_rejected_results)

        return jsonify({'latest_details': result})

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
