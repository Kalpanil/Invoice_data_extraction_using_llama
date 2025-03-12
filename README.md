## Overview
The Invoice Extraction System is a Streamlit-based web application that extracts structured data from scanned PDF invoices using OCR and AI (LLaMA 3.2). The extracted data is stored in an MSSQL database and can be retrieved or downloaded when needed.

## Features
- Upload scanned PDF invoices for processing.
- Extract key invoice details using OCR (Tesseract) and AI-based text processing (LLaMA 3.2 via Ollama).
- Validate extracted data using Pydantic models.
- Store invoice details and PDFs in an MSSQL database.
- Retrieve and download stored invoices from the database.

## Technologies Used
- **Python**
- **Streamlit** (Web UI)
- **OCR**: Pytesseract, OpenCV
- **AI Model**: LLaMA 3.2 (via Ollama)
- **Database**: MSSQL (via PyODBC)
- **PDF Processing**: pdf2image
- **Validation**: Pydantic

## Installation

### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- MSSQL Server (with ODBC Driver 17)
- Tesseract OCR (Install from https://github.com/UB-Mannheim/tesseract/wiki)
- Ollama (for LLaMA inference)

### Install Dependencies
```sh
pip install streamlit pytesseract opencv-python numpy pdf2image pyodbc pydantic ollama
```

### Configure Database
Create an MSSQL database named `InvoiceDB` and a table `Invoices`:
```sql
CREATE TABLE Invoices (
    invoice_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    invoice_no VARCHAR(50),
    invoice_date DATE,
    Total_amt FLOAT,
    CurrencyType VARCHAR(10),
    Purchase_no VARCHAR(50),
    PDF_file VARBINARY(MAX),
    filename VARCHAR(255)
);
```

## Running the Application
Start the Streamlit app:
```sh
streamlit run app.py
```

## Output ScreenShots
![image](https://github.com/user-attachments/assets/4beb1227-b475-41d5-88d1-ed764cbc8713)

## Usage
1. **Upload PDFs**: Select and upload scanned invoice PDFs.
2. **Process Invoices**: Click "Process Selected PDFs" to extract invoice details.
3. **Save to Database**: After processing, click "Save to Database" to store extracted data.
4. **Retrieve Invoices**: Use the "Retrieve Invoices" section to list and download stored invoices.

## File Structure
```
Invoice-Extraction/
│-- app.py  # Main Streamlit application
│-- requirements.txt  # Python dependencies
│-- README.md  # Project documentation
│-- temp_uploads/  # Temporary directory for PDFs
```

## Troubleshooting
- **OCR issues?** Ensure Tesseract is installed and added to the system PATH.
- **Database connection issues?** Check MSSQL server settings and ODBC driver installation.
- **AI model not working?** Ensure Ollama is running and LLaMA 3.2 is installed.

## Future Enhancements
- Add support for multiple invoice layouts using deep learning.
- Improve text extraction accuracy with fine-tuned OCR models.
- Implement user authentication for better security.

## License
This project is open-source under the MIT License.

## Contatct Us
kalpanil22kanbarkar@gmail.com 
