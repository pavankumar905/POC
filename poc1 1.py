from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import google.generativeai as genai
from sqlalchemy import create_engine, text
import json
app = Flask(__name__)
cors = CORS(app, origins='*')

querylist=[]
# Load environment variables
load_dotenv()

#here is the gemini api key which is used to make api calls
api_key = "AIzaSyDypRRzb3bEOxHWcaJ3j7qtAbxdwfoNmeU"  # API key for genai

# Configure genai with the API key
genai.configure(api_key=api_key)

# DATABASE_URI = "postgresql://newatsdb_user:9kKKrXd7ka304O4YfmvZ1pIkC75Nhml9@dpg-cs3mdkrtq21c73dmgajg-a.singapore-postgres.render.com/newatsdb"


#Here we are connecting python code with mysql database
DATABASE_URI = "mysql+pymysql://root:teja@localhost:3306/pocdb"
engine = create_engine(DATABASE_URI)



USERS_FILE = 'users.json'


# print(query)
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            content = f.read()
            return json.loads(content) if content else {}
    return {}


def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)
        
        
#Here is the register end point
@app.route('/register', methods=['POST'])
def register():
    users = load_users()
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    name = request.json.get('name')
    mobile = request.json.get('mobile')

    # Check if the username already exists
    if username in users:
        return jsonify({"message": "Username already exists!"}), 400

    # Register the new user
    users[username] = {
    "email": email,
    "mobile": mobile,
    "password": password,
    "name": name
}
    save_users(users)
    return jsonify({"message": "User registered successfully!"}), 201





#here is the login end point
@app.route('/login', methods=['POST'])
def login():
    users = load_users()
    username = request.json.get('username')
    password = request.json.get('password')

    # Check if the user exists and the password matches
    if username in users and users[username]['password'] == password:
        return jsonify({"message": "Login successful!", "username": username}), 200
    else:
        return jsonify({"message": "Invalid username or password!"}), 401
    
        
#here is the reset_password endpoint
@app.route('/reset_password', methods=['POST'])
def reset_password():
    users = load_users()  # Load users from the JSON file
    username = request.json.get('username')
    email = request.json.get('email')  # Get the email from the request
    new_password = request.json.get('new_password')

    # Validate required fields
    if not all([username, email, new_password]):
        return jsonify({"message": "Username, email, and new password are required!"}), 400

    # Check if the user exists
    user = users.get(username)
    if not user:
        return jsonify({"message": "Invalid username!"}), 404

    # Check if the email matches the username
    if user['email'] != email:
        return jsonify({"message": "Email does not match the username!"}), 400

    # Update the user's password
    users[username]['password'] = new_password  # Store the new password in plaintext
    save_users(users)  # Save the updated user data back to the JSON file

    return jsonify({"message": "Password reset successfully!"}), 200   
 



#here is the endpoint that converts human language query to sql query and sql language to 
# human understandable text
@app.route('/generate-sql', methods=['POST'])
def generate_sql():
    query = request.json.get('query')
    querylist.append(query)
    
    #Here is the prompt given to the GEMINI API where we defined schemas of the 5 tables
    sql_query_prompt = f'''
    you are a helpful database assistant
    following are the tables and generate query
    
    CREATE TABLE `abbreviations` (   
    `Abbreviation` varchar(5) NOT NULL,
    `Full_text` varchar(50) DEFAULT NULL,
    `Practitioner_ID` int(10) DEFAULT NULL,
    `CreatedOn` datetime DEFAULT NULL,
    `CreatedBy` int(10) DEFAULT '0',
    `TS` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`Abbreviation`),
    UNIQUE KEY `Abbreviation` (`Abbreviation`) USING BTREE
    ) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=COMPACT;
        
        
    CREATE TABLE `access_restriction` (
    `Access_restriction_ID` int(10) NOT NULL AUTO_INCREMENT,
    `User_class_ID` int(10) DEFAULT NULL,
    `Program_to_restrict` varchar(6) DEFAULT NULL,
    `CreatedOn` datetime DEFAULT NULL,
    `CreatedBy` int(10) DEFAULT '0',
    `TS` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`Access_restriction_ID`),
    KEY `Access_restriction_ID` (`Access_restriction_ID`) USING BTREE,
    KEY `Program_to_restrict` (`Program_to_restrict`) USING BTREE
    ) ENGINE=InnoDB AUTO_INCREMENT=793703286 DEFAULT CHARSET=latin1 ROW_FORMAT=COMPACT;

    CREATE TABLE `accounts_category` (
    `Accounts_category_ID` int(10) NOT NULL AUTO_INCREMENT,
    `Accounts_category_number` varchar(3) DEFAULT NULL,
    `Accounts_category_text` varchar(30) DEFAULT NULL,
    `CreatedOn` datetime DEFAULT NULL,
    `CreatedBy` int(10) DEFAULT '0',
    `TS` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`Accounts_category_ID`),
    UNIQUE KEY `Accounts_category_number` (`Accounts_category_number`) USING BTREE
    ) ENGINE=InnoDB AUTO_INCREMENT=485 DEFAULT CHARSET=latin1 ROW_FORMAT=COMPACT;

    CREATE TABLE `agriabreedlist` (
    `AgriaBreedListID` int(11) NOT NULL AUTO_INCREMENT,
    `BreedName` varchar(255) DEFAULT NULL,
    `Species` varchar(255) DEFAULT NULL,
    `AgriaBreedID` int(11) DEFAULT NULL,
    PRIMARY KEY (`AgriaBreedListID`)
    ) ENGINE=InnoDB AUTO_INCREMENT=1422 DEFAULT CHARSET=latin1;

    CREATE TABLE `animal:edits` (
    `Edit_ID` int(11) NOT NULL AUTO_INCREMENT,
    `Edit_datetime` datetime DEFAULT NULL,
    `User_initials` varchar(255) DEFAULT '',
    `Workstation` varchar(255) DEFAULT '',
    `Animal_ID` int(11) NOT NULL,
    `Client_ID` int(10) DEFAULT NULL,
    `Species` varchar(20) DEFAULT NULL,
    `Breed` varchar(255) DEFAULT NULL,
    `Colour` varchar(30) DEFAULT NULL,
    `Markings` varchar(20) DEFAULT NULL,
    `Sex` varchar(1) DEFAULT NULL,
    `Neutered` tinyint(1) NOT NULL,
    `Date_of_birth` datetime DEFAULT NULL,
    `Height` decimal(10,3) DEFAULT NULL,
    `Weight` decimal(10,3) DEFAULT NULL,
    `Insurance_Co` varchar(20) DEFAULT NULL,
    `Insurance_policy_number` varchar(20) DEFAULT NULL,
    `Identity_number` varchar(20) DEFAULT NULL,
    `Operation_ID` int(10) DEFAULT NULL,
    `Overnight_charge` decimal(19,4) DEFAULT NULL,
    `Notes` varchar(5000) DEFAULT NULL,
    `Sensitive_notes` varchar(5000) DEFAULT NULL,
    `Warning_or_status_1` varchar(20) DEFAULT NULL,
    `Warning_or_status_2` varchar(20) DEFAULT NULL,
    `Warning_or_status_3` varchar(20) DEFAULT NULL,
    `Other_1` varchar(20) DEFAULT NULL,
    `Other_2` varchar(20) DEFAULT NULL,
    `Other_3` varchar(20) DEFAULT NULL,
    `Other_4` varchar(20) DEFAULT NULL,
    `Other_5` varchar(20) DEFAULT NULL,
    `Insurance_expiry_date` datetime DEFAULT NULL,
    `Inpatient` tinyint(1) NOT NULL,
    `Deceased` tinyint(1) NOT NULL,
    `MovedAway` tinyint(1) DEFAULT '0',
    `Animal_name` varchar(50) DEFAULT NULL,
    `CreatedOn` datetime DEFAULT NULL,
    `CreatedBy` int(10) DEFAULT '0',
    `TS` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `ProfilePicture` varchar(255) DEFAULT '',
    PRIMARY KEY (`Edit_ID`),
    KEY `Animal_ID` (`Animal_ID`) USING BTREE,
    KEY `Animal_name` (`Animal_name`) USING BTREE,
    KEY `Client_ID` (`Client_ID`) USING BTREE,
    KEY `Identity_number` (`Identity_number`) USING BTREE,
    KEY `Insurance_Co` (`Insurance_Co`) USING BTREE,
    KEY `Insurance_policy_number` (`Insurance_policy_number`) USING BTREE,
    KEY `Other_1` (`Other_1`) USING BTREE
    ) ENGINE=InnoDB AUTO_INCREMENT=47457 DEFAULT CHARSET=latin1 ROW_FORMAT=COMPACT;


    I will give a natural language query "{query}" to get details from the database, and you have to  change that query to an SQL query
    output should be only the SQL query, do not include any explanations, and analysis
    '''
    #we are using gemini-1.5-flash model
    model = genai.GenerativeModel('gemini-1.5-flash')

    #here we are giving the prompt to the gemini model
    response = model.generate_content(sql_query_prompt)

    # Print the generated SQL query
    #print(response.text)
    sqlquery=response.text
    #here we are cleaning sql query coming from gemini
    sqlquery=sqlquery.replace('```', '').replace('sql', '')
    print(sqlquery)
    try:
        with engine.connect() as connection:
            #here we are executing sql query from gemini in mysql
            result = connection.execute(text(sqlquery))
            #here we are getting results
            rows = result.fetchall()
            #print("Query results:", rows)
    except Exception as e:
        print("Error executing the SQL query:", e)
        
    #here  result from mysql is feeded again to gemini api to get the human understandable text
    #here also we need to give table schemas to gemini      
    human_text = f'''
    you have to convert database records to natural language text

    given are the tables
    CREATE TABLE `abbreviations` (
    `Abbreviation` varchar(5) NOT NULL,
    `Full_text` varchar(50) DEFAULT NULL,
    `Practitioner_ID` int(10) DEFAULT NULL,
    `CreatedOn` datetime DEFAULT NULL,
    `CreatedBy` int(10) DEFAULT '0',
    `TS` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`Abbreviation`),
    UNIQUE KEY `Abbreviation` (`Abbreviation`) USING BTREE
    ) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=COMPACT;
        
        
    CREATE TABLE `access_restriction` (
    `Access_restriction_ID` int(10) NOT NULL AUTO_INCREMENT,
    `User_class_ID` int(10) DEFAULT NULL,
    `Program_to_restrict` varchar(6) DEFAULT NULL,
    `CreatedOn` datetime DEFAULT NULL,
    `CreatedBy` int(10) DEFAULT '0',
    `TS` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`Access_restriction_ID`),
    KEY `Access_restriction_ID` (`Access_restriction_ID`) USING BTREE,
    KEY `Program_to_restrict` (`Program_to_restrict`) USING BTREE
    ) ENGINE=InnoDB AUTO_INCREMENT=793703286 DEFAULT CHARSET=latin1 ROW_FORMAT=COMPACT;

    CREATE TABLE `accounts_category` (
    `Accounts_category_ID` int(10) NOT NULL AUTO_INCREMENT,
    `Accounts_category_number` varchar(3) DEFAULT NULL,
    `Accounts_category_text` varchar(30) DEFAULT NULL,
    `CreatedOn` datetime DEFAULT NULL,
    `CreatedBy` int(10) DEFAULT '0',
    `TS` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`Accounts_category_ID`),
    UNIQUE KEY `Accounts_category_number` (`Accounts_category_number`) USING BTREE
    ) ENGINE=InnoDB AUTO_INCREMENT=485 DEFAULT CHARSET=latin1 ROW_FORMAT=COMPACT;

    CREATE TABLE `agriabreedlist` (
    `AgriaBreedListID` int(11) NOT NULL AUTO_INCREMENT,
    `BreedName` varchar(255) DEFAULT NULL,
    `Species` varchar(255) DEFAULT NULL,
    `AgriaBreedID` int(11) DEFAULT NULL,
    PRIMARY KEY (`AgriaBreedListID`)
    ) ENGINE=InnoDB AUTO_INCREMENT=1422 DEFAULT CHARSET=latin1;    

    CREATE TABLE `animal:edits` (
    `Edit_ID` int(11) NOT NULL AUTO_INCREMENT,
    `Edit_datetime` datetime DEFAULT NULL,
    `User_initials` varchar(255) DEFAULT '',
    `Workstation` varchar(255) DEFAULT '',
    `Animal_ID` int(11) NOT NULL,
    `Client_ID` int(10) DEFAULT NULL,
    `Species` varchar(20) DEFAULT NULL,
    `Breed` varchar(255) DEFAULT NULL,
    `Colour` varchar(30) DEFAULT NULL,
    `Markings` varchar(20) DEFAULT NULL,
    `Sex` varchar(1) DEFAULT NULL,
    `Neutered` tinyint(1) NOT NULL,
    `Date_of_birth` datetime DEFAULT NULL,
    `Height` decimal(10,3) DEFAULT NULL,
    `Weight` decimal(10,3) DEFAULT NULL,
    `Insurance_Co` varchar(20) DEFAULT NULL,
    `Insurance_policy_number` varchar(20) DEFAULT NULL,
    `Identity_number` varchar(20) DEFAULT NULL,
    `Operation_ID` int(10) DEFAULT NULL,
    `Overnight_charge` decimal(19,4) DEFAULT NULL,
    `Notes` varchar(5000) DEFAULT NULL,
    `Sensitive_notes` varchar(5000) DEFAULT NULL,
    `Warning_or_status_1` varchar(20) DEFAULT NULL,
    `Warning_or_status_2` varchar(20) DEFAULT NULL,
    `Warning_or_status_3` varchar(20) DEFAULT NULL,
    `Other_1` varchar(20) DEFAULT NULL,
    `Other_2` varchar(20) DEFAULT NULL,
    `Other_3` varchar(20) DEFAULT NULL,
    `Other_4` varchar(20) DEFAULT NULL,
    `Other_5` varchar(20) DEFAULT NULL,
    `Insurance_expiry_date` datetime DEFAULT NULL,
    `Inpatient` tinyint(1) NOT NULL,
    `Deceased` tinyint(1) NOT NULL,
    `MovedAway` tinyint(1) DEFAULT '0',
    `Animal_name` varchar(50) DEFAULT NULL,
    `CreatedOn` datetime DEFAULT NULL,
    `CreatedBy` int(10) DEFAULT '0',
    `TS` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `ProfilePicture` varchar(255) DEFAULT '',
    PRIMARY KEY (`Edit_ID`),
    KEY `Animal_ID` (`Animal_ID`) USING BTREE,
    KEY `Animal_name` (`Animal_name`) USING BTREE,
    KEY `Client_ID` (`Client_ID`) USING BTREE,
    KEY `Identity_number` (`Identity_number`) USING BTREE,
    KEY `Insurance_Co` (`Insurance_Co`) USING BTREE,
    KEY `Insurance_policy_number` (`Insurance_policy_number`) USING BTREE,
    KEY `Other_1` (`Other_1`) USING BTREE
    ) ENGINE=InnoDB AUTO_INCREMENT=47457 DEFAULT CHARSET=latin1 ROW_FORMAT=COMPACT;

        

    this is the query in natural language by human "{query}" and got records from the database is{rows} analyse this {rows} and give me in text format
    the output should be precise dont give any extra information
    '''

    #final result which is human understandable text we will get from gemini
    #In total we are making 2 gemini api call 
    response_final = model.generate_content(human_text)
    print(response_final.text)
    return jsonify({"querylist": querylist, "response": response_final.text}), 200
    


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1919, debug=True)

#Breif work flow of this backend code 

# 1)first we give human language text to get data from database
# 2)this human language text is fed to gemini to get actual sql query
# 3)this sql query is exctuded from python on mysql and we get some data
# 4)this data is again fed to gemini to get human understandable text






