import streamlit as st
import json
import pyodbc
from pydantic import BaseModel, Field, ValidationError
import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_path
import ollama
import re
import os
import base64

# Define Pydantic model
class Invoice(BaseModel):
    invoice_no: str = Field(..., title="Invoice Number")
    invoice_date: str = Field(..., title="Invoice Date")
    Total_amt: float = Field(..., title="Total Invoice Amount")
    CurrencyType: str
    Purchase_no: str = Field("UNKNOWN", title="Purchase Order Number")


# Database connection function
def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=KALPANIL;'
        'DATABASE=InvoiceDB;'
        'Trusted_Connection=yes;'
        'TrustServerCertificate=yes;'
        'Encrypt=no;' 
    )
    return conn

import pyodbc
import os
import streamlit as st

def store_in_database(invoice_data, pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            pdf_data = file.read()

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO Invoices (invoice_id, invoice_no, invoice_date, Total_amt, CurrencyType, Purchase_no, PDF_file, filename)
        VALUES (NEWID(), ?, ?, ?, ?, ?, ?, ?)
        """

        filename = os.path.basename(pdf_path)
        
        cursor.execute(query, 
                       invoice_data.invoice_no, 
                       invoice_data.invoice_date, 
                       invoice_data.Total_amt, 
                       invoice_data.CurrencyType, 
                       invoice_data.Purchase_no,
                       pyodbc.Binary(pdf_data),  # Ensure binary storage
                       filename)
        
        conn.commit()
        cursor.close()
        conn.close()
        st.success(f"Invoice {invoice_data.invoice_no} saved successfully!")

    except Exception as e:
        st.error(f"Database Insertion Error: {str(e)}")



# Function to process PDFs and extract text
def process_pdf(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)
    full_text = ""
    for i, image in enumerate(images):
        img = np.array(image)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray).strip()
        full_text += f"\n--- Page {i+1} ---\n{text}"
    return full_text

# Function to call LLaMA 3.2 via Ollama
def extract_invoice_data(full_text):
    prompt = f"""
    Extract structured data from the following invoice text:

    {full_text}

    ### Instructions:
    - Extract only the required fields.
    - Return output strictly as a **valid JSON** object, with **no explanations, extra text, or formatting issues**.
    - If a field is missing, return `"UNKNOWN"` instead of leaving it blank.

    ### **Required JSON Format:**
    {{
        "invoice_no": "string",       # Invoice number (e.g., "INV-12345")
        "invoice_date": "YYYY-MM-DD", # Invoice date in YYYY-MM-DD format
        "Total_amt": digits,           # no currency symbols
        "CurrencyType": "string",     # Currency type (default: "INR" if missing)
        "Purchase_no": "string"       # Customer purchase order number (PO No)
    }}

    ### **Important Rules:**
    - The response **must be valid JSON**. No additional text, explanations, or comments.
    - The **invoice_date must be formatted as YYYY-MM-DD**.
    - The **Total_amt must be as it is**
    - If a field is missing from the invoice, return `"UNKNOWN"`, **not null or empty strings**.
    - Ensure all fields are always present in the response.

    **Example Output:**
    ```json
    {{
        "invoice_no": "INV-12345",
        "invoice_date": "2025-03-05",
        "Total_amt": 1250.50,
        "CurrencyType": "INR",
        "Purchase_no": "PO-7890"
    }}
    """

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )
    raw_output = response["message"]["content"]
    json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)  # Post processing
    return json.loads(json_match.group(0)) if json_match else {}

# Function to create temporary directory if it doesn't exist
def ensure_temp_dir():
    temp_dir = "temp_uploads"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir

# Streamlit UI
st.title("Invoice Extraction System")

uploaded_files = st.file_uploader("Upload Invoice PDFs", type=["pdf"], accept_multiple_files=True)



# Reorganize the UI flow
if uploaded_files:
    processed_files = []
    temp_dir = ensure_temp_dir()
    
    process_button = st.button("Process Selected PDFs")
    
    if process_button:
        for uploaded_file in uploaded_files:
            # Processing code (unchanged)
            pdf_path = os.path.join(temp_dir, uploaded_file.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())
            
            st.write(f"Processing: {uploaded_file.name}...")
            extracted_text = process_pdf(pdf_path)
            
            # Extract data
            extracted_data = extract_invoice_data(extracted_text)
            try:
                invoice_data = Invoice(**extracted_data)
                # Store invoice data and pdf path for later database insertion
                processed_files.append((invoice_data, pdf_path))
                
                # Display the extracted data
                st.json(invoice_data.model_dump())
                
                
                # Display PDF preview
                with st.expander(f"Preview PDF: {uploaded_file.name}"):
                    # Convert first page to image for preview
                    images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
                    if images:
                        st.image(images[0], caption=f"Preview of {uploaded_file.name}", width=400)
            
            except ValidationError as e:
                st.error(f"Invalid extracted data from {uploaded_file.name}. Check LLaMA response.")
                st.error(str(e))
        
        # Store the processed files in session state
        if processed_files:
            st.session_state.processed_files = processed_files
            st.success("Processing complete! Click 'Save to Database' to store the invoices.")
    
    # Only show save button if we have processed files in session state
    if 'processed_files' in st.session_state and st.session_state.processed_files:
        save_button = st.button("Save to Database")
        if save_button:
            for invoice_data, pdf_path in st.session_state.processed_files:
                try:
                    # Improved error handling in database storage
                    store_in_database(invoice_data, pdf_path)
                except Exception as e:
                    st.error(f"Error saving {invoice_data.invoice_no}: {str(e)}")
            
            # Clear the session state after saving
            st.session_state.processed_files = []
            st.success("Database operations completed!")             
    
    if st.button("Clear All"):
        # Clean up temporary files
        for file in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, file))
            except:
                pass
        st.rerun()

def get_invoice_list():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if 'filename' exists
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Invoices' AND COLUMN_NAME = 'filename'
    """)
    column_exists = cursor.fetchone() is not None

    # Adjust the query based on the column existence
    if column_exists:
        query = "SELECT invoice_no, invoice_date, Total_amt, filename FROM Invoices ORDER BY invoice_date DESC"
    else:
        query = "SELECT invoice_no, invoice_date, Total_amt FROM Invoices ORDER BY invoice_date DESC"

    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

# Function to retrieve PDF by invoice number - also move to global scope
def get_pdf_by_invoice(invoice_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT PDF_file, filename FROM Invoices WHERE invoice_no = ?", (invoice_no,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result
    
with st.expander("Retrieve Invoices from Database"):
    st.subheader("Retrieve Invoice PDFs")
    
    # Show invoices button
    if st.button("Show Available Invoices"):
        # Get invoice list and store in session state
        st.session_state.invoices = get_invoice_list()
    
    # Display invoices if they exist in session state
    if 'invoices' in st.session_state and st.session_state.invoices:
        st.write("Select an invoice to download:")
        
        # Use radio buttons, selectbox or other component instead of buttons in a loop
        options = [f"{inv[3]} - Invoice #{inv[0]} ({inv[1]}) - {inv[2]}" for inv in st.session_state.invoices]
        selected_invoice = st.selectbox("Choose an invoice:", options)
        
        if selected_invoice:
            # Extract invoice number from the selected option
            selected_invoice_no = selected_invoice.split("Invoice #")[1].split(" ")[0]
            
            # Download button (outside the loop)
            if st.button("Download Selected Invoice"):
                pdf_data, original_filename = get_pdf_by_invoice(selected_invoice_no)
                
                # Provide download link
                b64_pdf = base64.b64encode(pdf_data).decode()
                href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{original_filename}">Download PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
    elif 'invoices' in st.session_state and not st.session_state.invoices:
        st.info("No invoices found in the database.")