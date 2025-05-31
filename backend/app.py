import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from models import db, User, Payment
from config import Config

app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')
app.config.from_object(Config)
CORS(app, supports_credentials=True)

db.init_app(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/api/register', methods=['POST'])
def register():
    data = request.form
    file = request.files.get('evidence')
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid or missing file'}), 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    # Save user and payment
    user = User(
        full_name=data.get('full_name'),
        email=data.get('email'),
        phone=data.get('phone')
    )
    db.session.add(user)
    db.session.commit()
    payment = Payment(
        user_id=user.id,
        amount=int(data.get('amount', 0)),
        payment_type=data.get('payment_type'),
        evidence_filename=filename
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify({'message': 'Registration successful'})

@app.route('/api/delegates', methods=['GET'])
def delegates():
    users = User.query.all()
    return jsonify([
        {
            'full_name': u.full_name,
            'email': u.email,
            'phone': u.phone,
            'registered_at': u.registered_at,
            'payment_type': u.payment.payment_type if u.payment else None,
            'evidence_filename': u.payment.evidence_filename if u.payment else None
        } for u in users
    ])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Serve React frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
