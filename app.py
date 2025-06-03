from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'jen123'  

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            address TEXT,
            profile_picture TEXT
        )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password, name, birthday, address):
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO users (username, password, name, age, address) VALUES (?, ?, ?, ?, ?)',
            (username, generate_password_hash(password), name, birthday, address)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_profile_picture(username, picture_path):
    conn = get_db_connection()
    conn.execute('UPDATE users SET profile_picture = ? WHERE username = ?', (picture_path, username))
    conn.commit()
    conn.close()

def check_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return user
    return None

def get_user_profile(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

# Initialize database
init_db()

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        birthday = request.form['birthday']
        address = request.form['address']
        profile_picture = request.files.get('profile_picture')
        picture_path = None
        if profile_picture and profile_picture.filename != '':
            upload_folder = os.path.join('static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            picture_path = os.path.join(upload_folder, profile_picture.filename)
            profile_picture.save(picture_path)
            picture_path = '/' + picture_path.replace('\\', '/').replace(' ', '%20')
        if register_user(username, password, name, birthday, address):
            if picture_path:
                update_profile_picture(username, picture_path)
            session['username'] = username
            return redirect(url_for('profile'))
        else:
            flash('Username already exists!')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = check_user(username, password)
        if user:
            session['username'] = username
            return redirect(url_for('profile'))
        else:
            flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = get_user_profile(session['username'])
    age = None
    if user and user['age']:
        try:
            birthday = datetime.strptime(user['age'], '%Y-%m-%d')
            today = datetime.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        except Exception:
            age = 'N/A'
    return render_template('profile.html', user=user, age=age)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True) 