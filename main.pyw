import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
from fpdf import FPDF
from datetime import datetime
from pathlib import Path

##GUID AppId={{C7184676-EB4C-485A-BB98-DEBD3B1376C4}

# Load environment variables from .env file
load_dotenv()

packing_list_assets = []  # Holds the selected assets


# MySQL Connection Setup
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
        messagebox.showerror("Database Connection Error", str(e))
        return None

# Initialize Database Schema
def initialize_database():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()

        # Create the assets table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            asset_id INT AUTO_INCREMENT PRIMARY KEY,
            asset_type VARCHAR(50),
            serial_number VARCHAR(100),
            assigned_to VARCHAR(100),
            location VARCHAR(100),
            status VARCHAR(50),
            charger_status VARCHAR(50),
            phone_number VARCHAR(15),
            carrier VARCHAR(50),
            host_name VARCHAR(100)
        )
        """)

        # Create the transactions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INT AUTO_INCREMENT PRIMARY KEY,
            asset_id INT,
            transaction_type VARCHAR(50),
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            user VARCHAR(100)
        )
        """)

        conn.commit()
        conn.close()


# Fetch Branches for Dropdown
def fetch_branches():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT city FROM branches")
        branches = [row[0] for row in cursor.fetchall()]
        conn.close()
        return branches
    return []
def fetch_depot():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Fuquay Varina,Smithfield FROM branches")
        depot = [row[0] for row in cursor.fetchall()]
        conn.close()
        return depot

# GUI Application
def main():
        initialize_database()

def add_asset():
    asset_type = asset_type_var.get()
    serial_number = serial_number_var.get()
    location = location_var.get()
    charger_status = charger_status_var.get()
    phone_number = phone_number_var.get()  # Optional field
    carrier = carrier_var.get()  # Optional field
    host_name = host_name_var.get()  # Optional field
    status = status_var.get()  # Get the selected status from the dropdown
    assigned_to = assigned_to_var.get()  # Assigned to field

    if asset_type and serial_number and location and charger_status:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO assets (asset_type, serial_number, assigned_to, location, status, charger_status, phone_number, carrier, host_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (asset_type, serial_number, assigned_to, location, status, charger_status, phone_number, carrier, host_name))
            conn.commit()
            conn.close()
            refresh_assets()
            messagebox.showinfo("Success", "Asset added successfully")
    else:
        messagebox.showwarning("Input Error", "Please fill in all required fields.")

# Refresh Assets Function

def refresh_assets():
        for row in tree.get_children():
            tree.delete(row)
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = "SELECT * FROM assets"
            search_text = search_var.get().strip()
            if search_text:
                query += " WHERE asset_type LIKE %s OR serial_number LIKE %s OR assigned_to LIKE %s OR location LIKE %s"
                cursor.execute(query, ('%' + search_text + '%', '%' + search_text + '%', '%' + search_text + '%', '%' + search_text + '%'))
            else:
                cursor.execute(query)
            for asset in cursor.fetchall():
                tree.insert("", "end", values=asset)
            conn.close()

def edit_asset():
    selected_item = tree.selection()
    if selected_item:
        selected_asset_id = tree.item(selected_item[0], 'values')
        if selected_asset_id:  # Ensure valid data is retrieved
            try:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    UPDATE assets
                    SET asset_type = %s, serial_number = %s, assigned_to = %s, location = %s, status = %s, charger_status = %s, phone_number = %s, carrier = %s, host_name = %s
                    WHERE asset_id = %s
                    """, (asset_type_var.get(), serial_number_var.get(), assigned_to_var.get(), location_var.get(),
                          status_var.get(), charger_status_var.get(), phone_number_var.get(), carrier_var.get(),
                          host_name_var.get(), selected_asset_id[0]))
                    conn.commit()
                    conn.close()
                    refresh_assets()
                    messagebox.showinfo("Success", "Asset updated successfully.")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Selection Error", "Selected asset contains no data.")
    else:
        messagebox.showwarning("Selection Error", "Please select an asset to edit.")



def assign_asset():
        selected_item = tree.selection()
        if selected_item:
            asset_id = tree.item(selected_item[0], 'values')[0]
            assigned_to = assigned_to_var.get()
            receiving_branch = receiving_branch_var.get()
            if assigned_to and receiving_branch:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE assets SET assigned_to = %s, status = 'Assigned', location = %s WHERE asset_id = %s",
                                   (assigned_to, receiving_branch, asset_id))
                    cursor.execute("INSERT INTO transactions (asset_id, transaction_type, user) VALUES (%s, 'Assign', %s)",
                                   (asset_id, assigned_to))
                    conn.commit()
                    conn.close()
                    refresh_assets()
                    messagebox.showinfo("Success", "Asset assigned and shipped successfully")
            else:
                messagebox.showwarning("Input Error", "Please specify a user and receiving branch.")
        else:
            messagebox.showwarning("Selection Error", "Please select an asset to assign.")


    # Packing Slip Function
def create_packing_slip():
    selected_item = tree.selection()
    if selected_item:
        asset_details = tree.item(selected_item[0], 'values')
        if asset_details:  # Ensure valid data is retrieved
            receiving_branch = receiving_branch_var.get()
            charger_status = asset_details[6]
            shipping_branch = shipping_branch_var.get()
            phone_number = asset_details[7]
            carrier = asset_details[8]
            host_name = asset_details[9]
            assigned_to = asset_details[3]
            status = status_var.get()

            # Initialize FPDF instance
            pdf = FPDF()
            pdf.set_margins(10, 10, 10)
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # Add Logo
            pdf.image("images/logowhite.png", x=60, y=10, w=50,)  # Resize logo and center it

            # Add Title
            pdf.set_font("Arial", size=20, style="B")  # Larger, bold font for the title
            pdf.cell(200, 15, txt="Packing Slip", ln=True, align='C')  # Adjust cell height
            pdf.ln(10)  # Add additional spacing

            # Asset Details in Grid
            pdf.set_font("Arial", size=12)
            details = [
                ("Asset ID:", asset_details[0]),
                ("Type:", asset_details[1]),
                ("Serial:", asset_details[2]),
                ("Assigned To:", assigned_to),
                ("Shipping Branch:", shipping_branch),
                ("Receiving Branch:", receiving_branch),
                ("Status:", status),
                ("Charger Status:", charger_status),
                ("Phone Number:", phone_number),
                ("Carrier:", carrier),
                ("Host Name:", host_name),
            ]

            for field, value in details:
                pdf.cell(50, 10, field, 1)
                pdf.cell(140, 10, str(value), 1, ln=1)

            # Add Disclaimer
            pdf.set_font("Arial", size=20)
            pdf.cell(200, 15, txt="Disclaimer:", ln=True, align='C')  # Adjust cell height
            pdf.set_font("Arial", size=10)
            
            disclaimer_text = (
                "Please verify that all hardware listed in your order or repair request has been received. "
                "If any item is missing, contact support immediately. "
                "For repair requests, ensure that all requested hardware, including chargers if specified, is returned. "
                "Failure to do so may result in delays or additional charges."
            )


            # Add centered disclaimer
         
            pdf.multi_cell(0, 10, disclaimer_text, align='C')

            subfolder = Path.home() / "Documents" / "packing_slips"
            subfolder.mkdir(parents=True, exist_ok=True)

            # Save PDF in the subfolder
            pdf_output_path = os.path.join(subfolder, f"PackingSlip_Asset{asset_details[0]}.pdf")
            pdf.output(pdf_output_path)
            print(f"PDF saved at: {pdf_output_path}")  # Debugging print

            # Automatically open the PDF
            try:
                os.startfile(pdf_output_path)  # For Windows
            except FileNotFoundError:
                messagebox.showerror("Error", f"File not found: {pdf_output_path}")
        else:
            messagebox.showwarning("Selection Error", "Selected asset contains no data.")
    else:
        messagebox.showwarning("Selection Error", "Please select an asset.")


def add_to_packing_list():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select an asset to add.")
        return

    asset_details = tree.item(selected_item[0], 'values')
    if any(asset[0] == asset_details[0] for asset in packing_list_assets):  # Check for duplicates by Asset ID
        messagebox.showinfo("Info", "Asset is already in the packing list.")
        return

    packing_list_assets.append(asset_details)
    packing_list_tree.insert("", "end", values=asset_details)
    
    


def generate_packing_slip():
    if not packing_list_assets:
        messagebox.showwarning("Error", "Packing list is empty.")
        return

    # Initialize PDF
    pdf = FPDF()
    pdf.set_margins(10, 10, 10)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add Title
    pdf.set_font("Arial", size=20, style="B")
    pdf.cell(200, 15, txt="Packing Slip", ln=True, align='C')
    pdf.ln(10)

    # Table Header
    pdf.set_font("Arial", size=12, style="B")
    columns = ["Asset ID", "Type", "Serial", "Assigned To", "Location", "Status"]
    column_widths = [20, 40, 40, 40, 30]
    for col, width in zip(columns, column_widths):
        pdf.cell(width, 10, col, border=1, align='C')
    pdf.ln()

    # Table Content
    pdf.set_font("Arial", size=12)
    for asset in packing_list_assets:

        pdf.cell(column_widths[1], 10, asset[1], border=1)  # Type
        pdf.cell(column_widths[2], 10, asset[2], border=1)  # Serial
        pdf.cell(column_widths[3], 10, asset[3], border=1)  # Assigned To
        pdf.cell(column_widths[4], 10, asset[4], border=1)  # Location
        pdf.cell(column_widths[5], 10, asset[5], border=1)  # Status
        pdf.ln()

    # Add Disclaimer
    pdf.ln(10)
    disclaimer_text = (
        "Disclaimer: Please verify that all hardware listed in this packing slip has been received. "
        "For repair requests, return all requested items, including chargers if specified."
    )
    pdf.multi_cell(0, 10, disclaimer_text)

    # Define subfolder path and ensure it exists
    subfolder = Path.home() / "Documents" / "packing_slips"
    subfolder.mkdir(parents=True, exist_ok=True)

    # Save PDF
    pdf_output_path = subfolder / f"PackingSlip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(str(pdf_output_path))
    messagebox.showinfo("Success", f"Packing slip generated at: {pdf_output_path}")

    # Automatically open the PDF
    try:
        os.startfile(pdf_output_path)  # For Windows
    except FileNotFoundError:
        messagebox.showerror("Error", f"File not found: {pdf_output_path}")

    # Clear Packing List
    packing_list_assets.clear()
    for item in packing_list_tree.get_children():
        packing_list_tree.delete(item)


      
 
# Populate Fields Function and Parameters for selection 
def populate_fields(event):
        selected_item = tree.selection()
        if selected_item:
            asset_details = tree.item(selected_item[0], 'values')
            if len(asset_details) > 1:
                asset_type_var.set(asset_details[1])
            if len(asset_details) > 2:
                serial_number_var.set(asset_details[2])
            if len(asset_details) > 3:
                assigned_to_var.set(asset_details[3])
            if len(asset_details) > 4:
                location_var.set(asset_details[4])
            if len(asset_details) > 6:
                charger_status_var.set(asset_details[6])
            if len(asset_details) > 7:
                phone_number_var.set(asset_details[7])
            if len(asset_details) > 8:
                carrier_var.set(asset_details[8])
            if len(asset_details) > 9:
                host_name_var.set(asset_details[9])
            if len(asset_details) > 10:
                search_var.set(asset_details[10])
            if len(asset_details) > 5:
                status_var.set(asset_details[5])

            else:
                charger_status_var.set('') 
                
    #Clear Field Function and Parameters
def clear_fields():
        asset_type_var.set('')
        serial_number_var.set('')
        assigned_to_var.set('')
        location_var.set('')
        charger_status_var.set('')
        shipping_branch_var.set('')
        receiving_branch_var.set('')
        phone_number_var.set('')
        carrier_var.set('')
        host_name_var.set('')
        search_var.set('')
        
def clear_packing_list():
    packing_list_assets.clear()
    for item in packing_list_tree.get_children():
        packing_list_tree.delete(item)
    messagebox.showinfo("Info", "Packing list cleared.")


root = tk.Tk()
root.title("IT Asset Tracker")

    # Input Frame
input_frame = ttk.Frame(root)
input_frame.pack(pady=10)

# Action Frame
action_frame = ttk.Frame(root)
action_frame.pack(pady=10)

# First Column
ttk.Label(input_frame, text="Asset Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
asset_type_var = tk.StringVar()
asset_type_dropdown = ttk.Combobox(input_frame, textvariable=asset_type_var)
asset_type_dropdown['values'] = ["Laptop", "Desktop", "Tablet", "Mobile Phone", "Hot Spot", "Other"]
asset_type_dropdown.grid(row=0, column=1, padx=5, pady=5)
   

ttk.Label(input_frame, text="Serial Number:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
serial_number_var = tk.StringVar()
ttk.Entry(input_frame, textvariable=serial_number_var).grid(row=1, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="Location:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
location_var = tk.StringVar()
location_dropdown = ttk.Combobox(input_frame, textvariable=location_var)
location_dropdown['values'] = fetch_branches()
location_dropdown.grid(row=2, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="Charger Status:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
charger_status_var = tk.StringVar()
charger_status_dropdown = ttk.Combobox(input_frame, textvariable=charger_status_var)
charger_status_dropdown['values'] = ["Yes", "No", "Requested", "Not Required"]
charger_status_dropdown.grid(row=3, column=1, padx=5, pady=5)

# Status Dropdown
ttk.Label(input_frame, text="Status:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
status_var = tk.StringVar()
status_dropdown = ttk.Combobox(input_frame, textvariable=status_var)
status_dropdown['values'] = ["Available", "In Transit", "Assigned", "Under Repair", "Disposed"]  # Add other statuses if needed
status_dropdown.grid(row=4, column=1, padx=5, pady=5)
status_dropdown.current(0)  # Set default value

# Second Column
ttk.Label(input_frame, text="Phone Number:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
phone_number_var = tk.StringVar()
ttk.Entry(input_frame, textvariable=phone_number_var).grid(row=0, column=3, padx=5, pady=5)

ttk.Label(input_frame, text="Carrier:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
carrier_var = tk.StringVar()
carrier_dropdown = ttk.Combobox(input_frame, textvariable=carrier_var)
carrier_dropdown['values'] = ["N/A", "Verizon", "US Cellular", "Other"]
carrier_dropdown.grid(row=1, column=3, padx=5, pady=5)
  

ttk.Label(input_frame, text="Host Name:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
host_name_var = tk.StringVar()
ttk.Entry(input_frame, textvariable=host_name_var).grid(row=2, column=3, padx=5, pady=5)

# Add Buttons Side by Side
ttk.Button(input_frame, text="Add Asset", command=add_asset).grid(row=4, column=4, padx=15, pady=15)
ttk.Button(input_frame, text="Save Asset", command=edit_asset).grid(row=4, column=3, padx=15, pady=30)
ttk.Button(action_frame, text="Add to Packing List", command=add_to_packing_list).grid(row=4, column=0, padx=5, pady=5)
ttk.Button(action_frame, text="Clear Packing List", command=clear_packing_list).grid(row=4, column=2, padx=5, pady=5)

    # Search Frame
search_frame = ttk.Frame(root)
search_frame.pack(pady=5)

ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=5, pady=5)
search_var = tk.StringVar()
ttk.Entry(search_frame, textvariable=search_var).grid(row=0, column=1, padx=5, pady=5)
ttk.Button(search_frame, text="Search", command=refresh_assets).grid(row=0, column=2, padx=5, pady=5)


    # Asset Treeview
tree = ttk.Treeview(root, columns=("ID", "Type", "Serial", "Assigned To", "Location", "Status", "Charger Status"), show="headings")
tree.heading("ID", text="ID")
tree.column("ID", width=20)
tree.heading("Type", text="Type")
tree.column("Type", width=100)
tree.heading("Serial", text="Serial")
tree.column("Serial", width=100)
tree.heading("Assigned To", text="Assigned To")
tree.column("Assigned To", width=100)
tree.heading("Location", text="Location")   
tree.column("Location", width=100)
tree.heading("Status", text="Status")
tree.column("Status", width=100)
tree.heading("Charger Status", text="Charger Status")
tree.column("Charger Status", width=100)
tree.pack(pady=10)

    # Bind the selection event to populate fields
tree.bind("<<TreeviewSelect>>", populate_fields)

    # Action Frame
action_frame = ttk.Frame(root)
action_frame.pack(pady=10)

ttk.Label(action_frame, text="Assign To:").grid(row=0, column=0, padx=5, pady=5)
assigned_to_var = tk.StringVar()
ttk.Entry(input_frame, textvariable=assigned_to_var).grid(row=0, column=1, padx=5, pady=5)

ttk.Label(action_frame, text="Shipping Branch:").grid(row=1, column=0, padx=5, pady=5)
shipping_branch_var = tk.StringVar()
shipping_branch_dropdown = ttk.Combobox(action_frame, textvariable=shipping_branch_var)
shipping_branch_dropdown['values'] = fetch_branches()
shipping_branch_dropdown.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(action_frame, text="Receiving Branch:").grid(row=2, column=0, padx=5, pady=5)
receiving_branch_var = tk.StringVar()
receiving_branch_dropdown = ttk.Combobox(action_frame, textvariable=receiving_branch_var)
receiving_branch_dropdown['values'] = fetch_branches()
receiving_branch_dropdown.grid(row=2, column=1, padx=5, pady=5)


ttk.Button(action_frame, text="Clear", command=clear_fields).grid(row=3, column=6, padx=5, pady=5)

# Transaction Type Dropdown
ttk.Label(action_frame, text="Transaction Type:").grid(row=0, column=0, padx=5, pady=5)
transaction_type_var = tk.StringVar()
transaction_type_dropdown = ttk.Combobox(action_frame, textvariable=transaction_type_var)
transaction_type_dropdown['values'] = ["Default", "Assign", "Return", "Repair", "Dispose"]  # Add transaction types here
transaction_type_dropdown.grid(row=0, column=1, padx=5, pady=5)
transaction_type_dropdown.current(0)  # Default to the first option

# Packing List Section
packing_list_frame = ttk.Frame(root)
packing_list_frame.pack(pady=10)

ttk.Label(packing_list_frame, text="Packing List:").pack()

packing_list_tree = ttk.Treeview(packing_list_frame, columns=("ID", "Type", "Serial", "Assigned To", "Location", "Status"), show="headings")
packing_list_tree.heading("ID", text="ID")
packing_list_tree.column("ID", width=50)
packing_list_tree.heading("Type", text="Type")
packing_list_tree.column("Type", width=100)
packing_list_tree.heading("Serial", text="Serial")
packing_list_tree.column("Serial", width=100)
packing_list_tree.heading("Assigned To", text="Assigned To")
packing_list_tree.column("Assigned To", width=100)
packing_list_tree.heading("Location", text="Location")
packing_list_tree.column("Location", width=100)
packing_list_tree.heading("Status", text="Status")
packing_list_tree.column("Status", width=100)
packing_list_tree.pack()

# Add Buttons for Packing List
ttk.Button(action_frame, text="Generate Packing Slip", command=generate_packing_slip).grid(row=4, column=1, padx=5, pady=5)

def periodic_refresh():
    refresh_assets()
    root.after(10000, periodic_refresh)  # Refresh every 10 seconds

periodic_refresh()


refresh_assets()

root.mainloop()

if __name__ == "__main__":
        main()