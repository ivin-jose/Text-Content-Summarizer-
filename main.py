
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import requests
from flask_mysqldb import MySQL
from datetime import datetime
import mysql.connector
app = Flask(__name__)


# Mysql DataBase 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'somethingfishy1234'
app.config['MYSQL_DB'] = 'sm_project'
mysql = MySQL(app)


# The Secrete key
app.config['SECRET_KEY'] = "is my secret key"

#CURRENT DATE

current_date = datetime.now()

# Print the current date in a specific format
# 12-AUG-2021
today_date = current_date.strftime("%d-%b-%Y")


# Convert the string to a datetime object

# Format the datetime object as a string in the desired format
# 2024-01-26
package_date = current_date.strftime("%Y-%m-%d")


#Invalid pages

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html')

#Internal server error

@app.errorhandler(500)
def page_not_found(e):
	return render_template('errors/404.html')


@app.route('/summarizer.com')
def home():
	return render_template('home.html')

''' User Login '''

@app.route('/summarizer.com/login', methods=['POST', 'GET'])
def login():
    error_message = ''

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('userpassword')

        # Checking password and admin name 
        cursor = mysql.connection.cursor()
        query = "SELECT userid, name, email FROM users WHERE email = %s AND password = %s"
        values = (username, password)
        cursor.execute(query, values)
        result = cursor.fetchall()

        # fetching admin name 
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM users"
        cursor.execute(query)
        admins = cursor.fetchall()

        if len(result) > 0:
            session['userid'] = result[0][0]
            session['username'] = result[0][1]
            return render_template('home.html')
        else:
            error_message = "Invalid credentials"

    return render_template('login.html', error_message=error_message)


'''  Logout '''

@app.route('/summarizer.com/logout')
def logout():
    session.pop('userid', None)
    session.pop('username', None)
    return render_template('home.html')

''' Signup '''


@app.route('/summarizer.com/signup', methods=['POST', 'GET'])
def signup():
 if request.method == 'POST':
    name = request.form.get('name')
    password = request.form.get('password')
    email = request.form.get('email')
    cursor = mysql.connection.cursor()

    # Check if admin already exists
    query = "SELECT * FROM users WHERE email = %s"
    cursor.execute(query, (email,))
    admin = cursor.fetchone()

    # Fetch all admins again after adding the new one
    query = "SELECT * FROM users"
    cursor.execute(query)
    admins = cursor.fetchall()
    if admin:
        status_message = "Email already exists."
        return render_template('/signup.html', add_status_message=status_message)

    # Insert the new admin into the database
    insert_query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
    cursor.execute(insert_query, (name, email, password))
    mysql.connection.commit()

    status_message = "User signup successfully."
    # Fetch all admins again after adding the new one
    query = "SELECT * FROM users"
    cursor.execute(query)
    admins = cursor.fetchall()
    
    return render_template('/home.html', add_status_message=status_message)
 else:
    return render_template('/signup.html')


''' Summaerizer '''

@app.route('/summarizer.com/main-chat', methods=['POST', 'GET'])
def main_chat():
    if 'userid' in session:
        summ = ''
        if request.method == 'POST':
            sentance = request.form.get('content')
            session.pop('recording', None)

            # remove session['recording']
            try:
                # Insert the new admin into the database
                cursor = mysql.connection.cursor()
                insert_query = "INSERT INTO history (userid, content, dates) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (session['userid'], sentance, today_date))
                mysql.connection.commit()
            except Exception as e:
                print(e)
            message = ("summarize this content in english maximum 100 words : ", sentance)

            url = "https://chatgpt-42.p.rapidapi.com/conversationgpt4-2"

            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "system_prompt": "",
                "temperature": 0.9,
                "top_k": 5,
                "top_p": 0.9,
                "max_tokens": 256,
                "web_access": False
            }
            headers = {
                "x-rapidapi-key": "ffb1f70549msh4f6afa984fb4d18p133e17jsne63de69dbc36",
                "x-rapidapi-host": "chatgpt-42.p.rapidapi.com",
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers)

            print(response.json())
            summ = response.json()
            summ = summ.get('result')

        return render_template('summarizer.html', summ=summ)
    else:
        return redirect('/summarizer.com/login')


@app.route('/summarizer.com/main-chat-recorder', methods=['POST', 'GET'])
def main_chat_recorder():
    if 'userid' in session:
        import speech_recognition as sr

        # Initialize recognizer
        recognizer = sr.Recognizer()

        # Capture speech input from the microphone
        with sr.Microphone() as source:
            print("Say something:")
            audio = recognizer.listen(source)

        # Use Google Web Speech API for recognition
        try:
            speech =  recognizer.recognize_google(audio) 
            print("You said: " + recognizer.recognize_google(audio))
            print("You said : ", speech)
            session['recording'] = speech
        except sr.UnknownValueError:
            error = ("Audio is not clear! try again.")
            session['recording'] = error
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

    return redirect('/summarizer.com/main-chat')



''' History '''


@app.route('/summarizer.com/history')
def history():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM history WHERE userid = %s"
    cursor.execute(query, (str(session['userid'])))
    history = cursor.fetchall()

    return render_template('history.html', history=history)

# _______________________________________________________________________________________________________________________



@app.route('/summarizer.com/admin', methods=['POST', 'GET'])
def admin_login():
    if request.method == 'POST':
        name = request.form.get('username')
        password = request.form.get('userpassword')

        # Checking password and admin name 
        cursor = mysql.connection.cursor()
        query = "SELECT admin FROM admins WHERE admin = %s AND password = %s"
        values = (name, password)
        cursor.execute(query, values)
        result = cursor.fetchall()

        # fetching admin name 
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM admins"
        cursor.execute(query)
        admins = cursor.fetchall()

        if len(result) > 0:
            session['admin'] = result[0][0]
            return redirect('/summarizer.com/admin_dashboard')
        else:
            error_message = "Invalid credentials"        
    return render_template('admin/admin_login.html')


@app.route('/summarizer.com/admin_dashboard')
def admin_dashboard():
    if 'admin' in session:
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM admins"
        cursor.execute(query)
        users = cursor.fetchall()
        return render_template('admin/admin_dashboard.html', users=users)
    else:
        return redirect('/summarizer.com/admin')


@app.route('/summarizer.com/users_admin')
def users_admin():
    if 'admin' in session:
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM users"
        cursor.execute(query)
        users = cursor.fetchall()
        return render_template('admin/admin_users.html', users=users)
    else:
        return redirect('/summarizer.com/admin')


@app.route('/summarizer.com/adminhistory/<int:userid>')
def adminhistory(userid):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM history WHERE userid = %s"
    cursor.execute(query, (str(userid)))
    history = cursor.fetchall()

    return render_template('admin/history.html', history=history)

@app.route('/summarizer.com/adminuserremove/<int:userid>')
def adminuserremove(userid):
    cursor = mysql.connection.cursor()
    query = "DELETE  FROM users WHERE userid = %s"
    cursor.execute(query, (str(userid)))
    mysql.connection.commit()


    cursor = mysql.connection.cursor()
    query = "DELETE  FROM history WHERE userid = %s"
    cursor.execute(query, (str(userid)))
    mysql.connection.commit()
    

    return redirect('/summarizer.com/users_admin')


@app.route('/summarizer.com/adminhistoryremove/<int:userid>')
def adminhistoryremove(userid):
    cursor = mysql.connection.cursor()
    query = "DELETE  FROM history WHERE userid = %s"
    cursor.execute(query, (str(userid)))
    mysql.connection.commit()
    

    return redirect('/summarizer.com/users_admin')

    
