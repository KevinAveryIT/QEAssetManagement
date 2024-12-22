import os
from dotenv import load_dotenv
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QDialog, QFormLayout
)
from PySide6.QtCore import Qt
import mysql.connector
from mysql.connector import Error
from fpdf import FPDF
from datetime import datetime
from pathlib import Path
import subprocess


###GUID#### AppId={{C7184676-EB4C-485A-BB98-DEBD3B1376C4}

# Load environment variables
load_dotenv()

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return conn
    except Error as e:
        QMessageBox.critical(None, "Database Connection Error", str(e))
        return None

class AssetDialog(QDialog):
            def __init__(self, parent=None, asset_data=None):
                super().__init__(parent)
                self.setWindowTitle("Add/Edit Asset")
                self.setFixedSize(400, 450)

                self.asset_data = asset_data
                self.init_ui()
                if asset_data:
                    self.populate_fields()

            def init_ui(self):
                self.layout = QFormLayout(self)

                self.asset_type_input = QComboBox()
                self.asset_type_input.addItems(["Laptop", "Desktop", "Tablet", "Mobile Phone", "Hot Spot", "Other"])
                self.serial_input = QLineEdit()
                self.assigned_to_input = QLineEdit()
                self.location_input = QComboBox()
                self.populate_location_dropdown()
                self.phone_input = QLineEdit()
                self.host_name_input = QLineEdit()
                self.status_input = QComboBox()
                self.status_input.addItems(["Available", "In Transit", "Assigned", "Under Repair", "Disposed"])
                self.charger_input = QComboBox()
                self.charger_input.addItems(["Requested", "Not Requested", "Sent", "Missing"])
                self.carrier_input = QComboBox()
                self.carrier_input.addItems(["None","Verizon", "AT&T", "T-Mobile", "Sprint", "Other"])

                self.layout.addRow("Asset Type:", self.asset_type_input)
                self.layout.addRow("Serial Number:", self.serial_input)
                self.layout.addRow("Assigned To:", self.assigned_to_input)
                self.layout.addRow("Location:", self.location_input)
                self.layout.addRow("Phone Number:", self.phone_input)
                self.layout.addRow("Host Name:", self.host_name_input)
                self.layout.addRow("Status:", self.status_input)
                self.layout.addRow("Charger Status:", self.charger_input)
                self.layout.addRow("Carrier:", self.carrier_input)

                self.save_button = QPushButton("Save")
                self.save_button.clicked.connect(self.accept)
                self.layout.addWidget(self.save_button)

            def populate_location_dropdown(self):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT city FROM branches")
                    branches = [row[0] for row in cursor.fetchall()]
                    self.location_input.addItems(branches)
                    conn.close()

            def populate_fields(self):
                self.asset_type_input.setCurrentText(self.asset_data[1] if len(self.asset_data) > 1 else "")
                self.serial_input.setText(self.asset_data[2] if len(self.asset_data) > 2 else "")
                self.assigned_to_input.setText(self.asset_data[3] if len(self.asset_data) > 3 else "")
                self.location_input.setCurrentText(self.asset_data[4] if len(self.asset_data) > 4 else "")
                self.phone_input.setText(self.asset_data[5] if len(self.asset_data) > 5 else "")
                self.host_name_input.setText(self.asset_data[6] if len(self.asset_data) > 6 else "")
                self.status_input.setCurrentText(self.asset_data[7] if len(self.asset_data) > 7 else "")
                self.charger_input.setCurrentText(self.asset_data[8] if len(self.asset_data) > 8 else "")
                self.carrier_input.setCurrentText(self.asset_data[9] if len(self.asset_data) > 9 else "")

            def get_data(self):
                return {
                    "asset_type": self.asset_type_input.currentText(),
                    "serial_number": self.serial_input.text(),
                    "assigned_to": self.assigned_to_input.text(),
                    "location": self.location_input.currentText(),
                    "phone_number": self.phone_input.text(),
                    "host_name": self.host_name_input.text(),
                    "status": self.status_input.currentText(),
                    "charger_status": self.charger_input.currentText(),
                    "carrier": self.carrier_input.currentText()
                }

class AssetTrackerApp(QMainWindow):
        def __init__(self):
                super().__init__()
                self.setWindowTitle("IT Asset Tracker")
                self.setFixedSize(1000, 600)

                self.packing_list_assets = []
                main_widget = QWidget()
                main_layout = QVBoxLayout()

                title_layout = QHBoxLayout()
                logo_label = QLabel()
                #logo_label.setPixmap(QPixmap("images/logowhite.png").scaled(100, 100, Qt.KeepAspectRatio))  # Replace with actual path to logo
                title_label = QLabel("IT Asset Tracker")
                title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
                title_layout.addWidget(logo_label)
                title_layout.addWidget(title_label)
                title_layout.setAlignment(Qt.AlignCenter)
                main_layout.addLayout(title_layout)

                self.asset_table = QTableWidget(0, 9)
                self.asset_table.setColumnHidden(0, True)
                self.asset_table.setHorizontalHeaderLabels(["ID", "Type", "Serial", "Assigned To", "Location", "Phone", "Host Name", "Status","Charger Status","Carrier"])
                self.asset_table.setSelectionBehavior(QTableWidget.SelectRows)
                main_layout.addWidget(self.asset_table)

                actions_layout = QHBoxLayout()
                add_btn = QPushButton("Add Asset")
                add_btn.clicked.connect(self.add_asset)
                actions_layout.addWidget(add_btn)

                edit_btn = QPushButton("Edit Asset")
                edit_btn.clicked.connect(self.edit_asset)
                actions_layout.addWidget(edit_btn)

                refresh_btn = QPushButton("Refresh")
                refresh_btn.clicked.connect(self.refresh_assets)
                actions_layout.addWidget(refresh_btn)

                packing_list_btn = QPushButton("Add to Packing List")
                packing_list_btn.clicked.connect(self.add_to_packing_list)
                actions_layout.addWidget(packing_list_btn)

                generate_packing_btn = QPushButton("Generate Packing Slip")
                generate_packing_btn.clicked.connect(self.generate_packing_slip)
                actions_layout.addWidget(generate_packing_btn)

                main_layout.addLayout(actions_layout)

                search_layout = QHBoxLayout()
                search_input = QLineEdit()
                search_input.setPlaceholderText("Search assets...")
                search_button = QPushButton("Search")
                search_button.clicked.connect(lambda: self.search_assets(search_input.text()))
                search_layout.addWidget(search_input)
                search_layout.addWidget(search_button)
                main_layout.addLayout(search_layout)
                search_input.returnPressed.connect(lambda: self.search_assets(search_input.text()))
                clear_search_button = QPushButton("Clear")
                clear_search_button.clicked.connect(lambda: self.clear_search(search_input))
                search_layout.addWidget(clear_search_button)
                
                
                self.packing_list_table = QTableWidget(0, 7)
                self.packing_list_table.setHorizontalHeaderLabels(["ID", "Type", "Serial", "Assigned To", "Location", "Status","Carrier"])
                main_layout.addWidget(QLabel("Packing List:"))
                
                self.transaction_type_input = QComboBox()
                self.transaction_type_input.addItems(["New Hire", "Termination Return", "Surplus", "Repair"])
                main_layout.addWidget(QLabel("Transaction Type:"))
                main_layout.addWidget(self.transaction_type_input)
                
                main_layout.addWidget(self.packing_list_table)

                main_widget.setLayout(main_layout)
                self.setCentralWidget(main_widget)

                self.refresh_assets()

        def search_assets(self, query):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT asset_id, asset_type, serial_number, assigned_to, location, phone_number, host_name, status, charger_status FROM assets WHERE asset_type LIKE %s OR serial_number LIKE %s OR assigned_to LIKE %s OR location LIKE %s", (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
                    rows = cursor.fetchall()
                    self.asset_table.setRowCount(0)
                    for row in rows:
                        row_position = self.asset_table.rowCount()
                        self.asset_table.insertRow(row_position)
                        for col, data in enumerate(row):
                            self.asset_table.setItem(row_position, col, QTableWidgetItem(str(data)))
                    conn.close()
        def clear_search(self, search_input):
            search_input.clear()
            self.refresh_assets()

        def refresh_assets(self):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT asset_id, asset_type, serial_number, assigned_to, location, phone_number, host_name, status, charger_status, carrier FROM assets")
                    rows = cursor.fetchall()
                    self.asset_table.setRowCount(0)
                    for row in rows:
                        row_position = self.asset_table.rowCount()
                        self.asset_table.insertRow(row_position)
                        for col, data in enumerate(row):
                            self.asset_table.setItem(row_position, col, QTableWidgetItem(str(data)))
                    conn.close()

        def add_asset(self):
                dialog = AssetDialog(self)
                if dialog.exec():
                    data = dialog.get_data()
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO assets (asset_type, serial_number, assigned_to, location, phone_number, host_name, status, charger_status, carrier) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (data["asset_type"], data["serial_number"], data["assigned_to"], data["location"], data["phone_number"], data["host_name"], data["status"], data["charger_status"], data["carrier"])
                        )
                        conn.commit()
                        conn.close()
                        self.refresh_assets()

        def edit_asset(self):
                selected_row = self.asset_table.currentRow()
                if selected_row != -1:
                    asset = [
                        self.asset_table.item(selected_row, col).text() if self.asset_table.item(selected_row, col) else ""
                        for col in range(self.asset_table.columnCount())
                    ]
                    dialog = AssetDialog(self, asset)
                    if dialog.exec():
                        data = dialog.get_data()
                        conn = get_db_connection()
                        if conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE assets SET asset_type = %s, serial_number = %s, assigned_to = %s, location = %s, phone_number = %s, host_name = %s, status = %s, charger_status = %s, carrier = %s WHERE asset_id = %s",
                                (data["asset_type"], data["serial_number"], data["assigned_to"], data["location"], data["phone_number"], data["host_name"], data["status"], data["charger_status"], data["carrier"], asset[0])
                            )
                            conn.commit()
                            conn.close()
                            self.refresh_assets()

        def add_to_packing_list(self):
                selected_row = self.asset_table.currentRow()
                if selected_row != -1:
                    asset = [
                        self.asset_table.item(selected_row, col).text() if self.asset_table.item(selected_row, col) else ""
                        for col in range(self.asset_table.columnCount())
                    ]
                    if asset not in self.packing_list_assets:
                        self.packing_list_assets.append(asset)
                        row_position = self.packing_list_table.rowCount()
                        self.packing_list_table.insertRow(row_position)
                        for col, data in enumerate(asset[:6]):  # Only include relevant columns
                            self.packing_list_table.setItem(row_position, col, QTableWidgetItem(data))

        def generate_packing_slip(self):
                if not self.packing_list_assets:
                    QMessageBox.warning(self, "Error", "Packing list is empty.")
                    return

                pdf = FPDF()
                pdf.set_margins(10, 10, 10)
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                # Add Title and Logo
                pdf.image("images/logowhite.png", x=10, y=8, w=30)
                pdf.set_font("Arial", size=20, style="B")
                pdf.cell(200, 15, txt="Packing Slip", ln=True, align='C')
                pdf.set_font("Arial", size=14, style="B")
                pdf.cell(200, 10, txt=f"Transaction Type: {self.transaction_type_input.currentText()}", ln=True, align='C')  # Change dynamically

                # Add Table Header
                columns = ["Type", "Serial", "Assigned To", "Location", "Phone", "Host Name", "Charger Status"]
                column_widths = [40, 40, 40, 30, 40, 40, 40]
                pdf.set_font("Arial", size=12, style="B")
                for col, width in zip(columns, column_widths):
                    pdf.cell(width, 10, col, border=1, align='C')
                pdf.ln()

                # Add Table Content
                pdf.set_font("Arial", size=12)
                for asset in self.packing_list_assets:
                    for col, data in enumerate(asset[:6]):
                        pdf.cell(column_widths[col], 10, str(data), border=1)
                        pdf.cell(column_widths[4], 10, str(asset[5]), border=1)  # Phone
                    pdf.cell(column_widths[5], 10, str(asset[6]), border=1)  # Host Name
                    pdf.cell(column_widths[6], 10, str(asset[7]), border=1)  # Charger Status
                    pdf.ln()

                # Add Disclaimer
                disclaimer_text = (
                    "Disclaimer: Please verify that all hardware listed in this packing slip has been received. "
                    "For repair requests, return all requested items, including chargers if specified."
                )
                pdf.ln(10)
                pdf.multi_cell(0, 10, disclaimer_text)

                # Save the PDF
                subfolder = Path.home() / "Documents" / "packing_slips"
                subfolder.mkdir(parents=True, exist_ok=True)
                pdf_output_path = subfolder / f"PackingSlip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf.output(str(pdf_output_path))

                # Open the PDF
                try:
                    if os.name == 'nt':
                        os.startfile(str(pdf_output_path))  # Windows
                    elif os.name == 'posix':
                        subprocess.run(['xdg-open', str(pdf_output_path)])  # Linux
                    elif os.name == 'darwin':
                        subprocess.run(['open', str(pdf_output_path)])  # macOS
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Unable to open PDF: {e}")

                # Clear the packing list
                self.packing_list_assets.clear()
                self.packing_list_table.setRowCount(0)

    
if __name__ == "__main__":
            app = QApplication([])
            window = AssetTrackerApp()
            window.show()
            app.exec()

