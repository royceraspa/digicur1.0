from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DATABASE = 'database.db'

# Initialize the database if not exists
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Connect to the database
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

# Create a new user in the database
def create_user(username, password, balance):
    db = get_db()
    hashed_password = generate_password_hash(password, method='sha256')
    db.execute('INSERT INTO users (username, password, balance) VALUES (?, ?, ?)', (username, hashed_password, balance))
    db.commit()

# Authenticate user
def authenticate_user(username, password):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if user and check_password_hash(user['password'], password):
        return {'authenticated': True, 'message': 'Authentication successful', 'balance': user['balance']}
    else:
        return {'authenticated': False, 'message': 'Authentication failed'}

# Get user balance
def get_balance(username):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if user:
        return {'balance': user['balance']}
    else:
        return {'balance': None, 'message': 'User not found'}

# Transfer funds between users
def transfer_funds(sender, receiver, amount):
    db = get_db()
    sender_info = db.execute('SELECT * FROM users WHERE username = ?', (sender,)).fetchone()
    receiver_info = db.execute('SELECT * FROM users WHERE username = ?', (receiver,)).fetchone()

    if sender_info and receiver_info and sender_info['balance'] >= amount:
        new_sender_balance = sender_info['balance'] - amount
        new_receiver_balance = receiver_info['balance'] + amount

        db.execute('UPDATE users SET balance = ? WHERE username = ?', (new_sender_balance, sender,))
        db.execute('UPDATE users SET balance = ? WHERE username = ?', (new_receiver_balance, receiver,))
        db.commit()
        return {'success': True, 'message': 'Funds transferred successfully'}
    else:
        return {'success': False, 'message': 'Insufficient funds or invalid user'}

# Routes

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    return jsonify(authenticate_user(username, password))

# Get balance route
@app.route('/get_balance', methods=['POST'])
def get_balance_route():
    data = request.get_json()
    username = data['username']
    return jsonify(get_balance(username))

# Transfer funds route
@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    sender = data['sender']
    receiver = data['receiver']
    amount = data['amount']
    return jsonify(transfer_funds(sender, receiver, amount))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
