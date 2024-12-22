from flask import Flask, render_template, request, jsonify
import mysql.connector
from fpdf import FPDF
import os
from datetime import datetime

app = Flask(__name__)

# Database connection

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

# Route to render the main page
@app.route('/')
def index():
    return render_template('index.html')

# API to get all assets
@app.route('/assets', methods=['GET'])
def get_assets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM assets")
    assets = cursor.fetchall()
    conn.close()
    return jsonify(assets)

# API to add a new asset
@app.route('/add_asset', methods=['POST'])
def add_asset():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO assets (asset_type, serial_number, assigned_to, location, phone_number, host_name, status, charger_status, carrier) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (data['asset_type'], data['serial_number'], data['assigned_to'], data['location'], data['phone_number'], 
         data['host_name'], data['status'], data['charger_status'], data['carrier'])
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# PDF generation for packing slip
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.json
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Packing Slip", ln=True, align='C')

    for asset in data['assets']:
        pdf.cell(200, 10, txt=f"{asset['asset_type']} - {asset['serial_number']} - {asset['assigned_to']}", ln=True)

    output_path = os.path.join(os.getcwd(), f"PackingSlip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    pdf.output(output_path)

    return jsonify({"success": True, "path": output_path})

if __name__ == '__main__':
    app.run(debug=True)
