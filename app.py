from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime

app = Flask(__name__)
# Setup SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iss_logs.db'
db = SQLAlchemy(app)

# Database Model
class Snapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.String(20))
    lon = db.Column(db.String(20))
    note = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Create the database file
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Fetch ISS Position
    iss_req = requests.get("http://api.open-notify.org/iss-now.json").json()
    # Fetch People in Space
    astro_req = requests.get("http://api.open-notify.org/astros.json").json()
    
    return render_template('index.html', 
                           iss=iss_req['iss_position'], 
                           count=astro_req['number'])

@app.route('/save', methods=['POST'])
def save():
    new_log = Snapshot(
        lat=request.form.get('lat'),
        lon=request.form.get('lon'),
        note=request.form.get('note')
    )
    db.session.add(new_log)
    db.session.commit()
    return redirect('/logs')

@app.route('/logs')
def logs():
    all_snapshots = Snapshot.query.order_by(Snapshot.timestamp.desc()).all()
    return render_template('logs.html', logs=all_snapshots)

if __name__ == '__main__':
    app.run(debug=True)