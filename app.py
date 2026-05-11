from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'orbital_secret_key' # Required for flashing messages

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
    # Default values to prevent front-end crashes (7.2 Missing Keys)
    iss_pos = {'latitude': '0.00', 'longitude': '0.00'}
    astro_count = 'N/A'
    
    try:
        # Fetch ISS Position
        iss_res = requests.get("http://api.open-notify.org/iss-now.json", timeout=5)
        # Fetch People in Space
        astro_res = requests.get("http://api.open-notify.org/astros.json", timeout=5)

        # 7.2 API Rate Limiting & Status Check
        if iss_res.status_code == 200 and astro_res.status_code == 200:
            iss_data = iss_res.json()
            astro_data = astro_res.json()
            
            # 7.2 Missing Keys Handling
            iss_pos = iss_data.get('iss_position', iss_pos)
            astro_count = astro_data.get('number', '0')
        else:
            # Fallback to last known position from DB
            last_log = Snapshot.query.order_by(Snapshot.timestamp.desc()).first()
            if last_log:
                iss_pos = {'latitude': last_log.lat, 'longitude': last_log.lon}
            flash("Live telemetry unavailable. Showing last known position.")

    except (requests.exceptions.RequestException, KeyError):
        # 7.2 Connection Errors
        flash("Live telemetry currently unavailable.")
        # Attempt fallback to DB even on connection failure
        last_log = Snapshot.query.order_by(Snapshot.timestamp.desc()).first()
        if last_log:
            iss_pos = {'latitude': last_log.lat, 'longitude': last_log.lon}
    
    return render_template('index.html', iss=iss_pos, count=astro_count)

@app.route('/save', methods=['POST'])
def save():
    # Capture inputs
    lat_raw = request.form.get('lat')
    lon_raw = request.form.get('lon')
    note = request.form.get('note')

    # 7.3 Hidden Field Integrity: Verify coordinates are valid numbers
    try:
        float(lat_raw)
        float(lon_raw)
    except (ValueError, TypeError):
        flash("Invalid coordinate data detected.")
        return redirect('/')

    # If valid, commit to database
    new_log = Snapshot(
        lat=lat_raw,
        lon=lon_raw,
        note=note
    )
    db.session.add(new_log)
    db.session.commit()
    flash("Snapshot saved successfully.")
    return redirect('/logs')

@app.route('/logs')
def logs():
    all_snapshots = Snapshot.query.order_by(Snapshot.timestamp.desc()).all()
    return render_template('logs.html', logs=all_snapshots)

if __name__ == '__main__':
    app.run(debug=True)