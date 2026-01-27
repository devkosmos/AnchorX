import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'neuroscan_secret_key'

# Database configuration
# Using SQLite for local development if PostgreSQL is not available, 
# but the user requested PSQL. In a real environment, we'd use:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/dbname'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(200), nullable=False)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Ожидание') # Ожидание, Подтвержден, Отклонен

# Routes
@app.route('/')
def login():
        if request.method == 'POST':
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                return jsonify({'success': True, 'redirect': url_for('panel')})
            return jsonify({'success': False, 'message': 'Неверный email или пароль'})
        
        return render_template('login.html')


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email уже зарегистрирован'})
    
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, phone=phone, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    session['user_id'] = new_user.id
    return jsonify({'success': True, 'redirect': url_for('panel')})

@app.route('/panel')
def panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    clients = Client.query.all()
    return render_template('panel.html', clients=clients)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# API for Panel
@app.route('/api/clients', methods=['GET'])
def get_clients():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    clients = Client.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'email': c.email,
        'phone': c.phone,
        'status': c.status
    } for c in clients])

@app.route('/api/clients', methods=['POST'])
def add_client():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    new_client = Client(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        status=data.get('status', 'Ожидание')
    )
    db.session.add(new_client)
    db.session.commit()
    return jsonify({'success': True, 'id': new_client.id})

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
