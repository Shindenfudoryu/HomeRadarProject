from crypt import methods
from flask import Flask, render_template, request, jsonify, redirect
from flask_httpauth import HTTPBasicAuth
import sqlite3
import base64
from SendEmailPicture import send_email_picture
from SendEmailTemperature import send_email_temperature
app = Flask(__name__)
auth = HTTPBasicAuth()

conn = sqlite3.connect("database.db")
cursor = conn.cursor()
conn.execute('''
    CREATE TABLE IF NOT EXISTS PicturesTaken (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image BLOB,
        datePicture DATE DEFAULT (DATE('now'))
    )
''')
conn.commit()
conn.close()
flag = False

user = {
    "": ""
}
temperature_value = 0.0
humidity_value = 0.0


@auth.verify_password
def verify_password(username, password):
    return user.get(username) == password


@app.route('/')
@auth.login_required
def index():
    return render_template('index.html', temperature=temperature_value, humidity=humidity_value)


@app.route('/update', methods=['POST'])
@auth.login_required
def update():
    global temperature_value
    global humidity_value

    try:
        # Extract float value from the request
        new_value_temperature = float(request.form['temperature'])
        new_value_humidity = float(request.form['humidity'])
        print(f'Received value: {new_value_temperature}')
        print(f'Received value: {new_value_humidity}')

        # Update the current value
        temperature_value = new_value_temperature
        humidity_value = new_value_humidity

        return 'OK', 200
    except Exception as e:
        print(f'Error: {e}')
        return 'Error', 500


@app.route('/get_value')
def get_value():
    global temperature_value
    global humidity_value
    return jsonify({'temp': temperature_value, 'humi': humidity_value})


@app.route('/trigger')
@auth.login_required
def trigger_action():
    global flag
    if flag:
        flag = False
        return "Action triggered!"
    else:
        return "Action not triggered!"


@app.route('/buttonPressed', methods=['GET'])
@auth.login_required
def buttonPressed_action():
    global flag
    flag = True
    return redirect('/')


@app.route('/upload', methods=['POST'])
@auth.login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        # Save the uploaded file to the database
        image_data = file.read()
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO images (image) VALUES (?)',
                       (sqlite3.Binary(image_data),))
        conn.commit()
        conn.close()
        return jsonify({'message': 'File uploaded and inserted into the database'})


@app.route('/sendEmailPicture', methods=['GET'])
@auth.login_required
def sendEmailPicture():
    send_email_picture()
    return "Email with Picture sent successfully"


@app.route('/sendEmailTemperature', methods=['GET'])
@auth.login_required
def sendEmailTemperature():
    global temperature_value
    send_email_temperature(temperature_value)
    return "Email with Temperature sent successfully"


@app.route('/gallery')
@auth.login_required
def image_gallery():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM images')
    images = cursor.fetchall()
    conn.close()

    # Convert binary image data to base64 for display in HTML
    for i, (image_id, image_data, image_date) in enumerate(images):
        images[i] = (image_id, base64.b64encode(
            image_data).decode('utf-8'), image_date)

    return render_template('gallery.html', images=images)


@app.route('/empty')
@auth.login_required
def delete_content():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM images')
    conn.commit()
    conn.close()
    return """Content deleted successfully from database <br> <a href="/">Go back to main page</a>"""
