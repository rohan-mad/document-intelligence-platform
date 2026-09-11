# Intelligent Document Extraction Platform

An AI-powered financial document extraction, validation, persistence and REST API platform.

## Features

- Upload PDF, JPG, JPEG and PNG documents
- Supports:
  - Invoice
  - Balance Sheet
  - Profit & Loss
  - Cash Flow Statement
- PDF text extraction using PyMuPDF
- OCR for scanned/image-based documents using Tesseract
- Structured AI extraction using OpenAI
- Evidence snippets and page references
- Financial consistency validation
- SQLite persistence
- REST APIs using FastAPI
- Swagger/OpenAPI documentation
- Web dashboard for upload and result inspection
- Raw JSON result view
- Automated validation tests

## Architecture

```text
User
  |
  v
Frontend Dashboard
  |
  v
FastAPI REST API
  |
  +--------------------------+
  |                          |
  v                          v
File Validation         OCR / Text Extraction
  |                          |
  +------------+-------------+
               |
               v
          AI Extraction
               |
               v
      Financial Validation
               |
               v
         SQLite Database
               |
               v
        JSON API Response
```

## Project Structure

```text
document-intelligence-platform/
|
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── api/
│       │   └── routes/
│       │       └── documents.py
│       ├── core/
│       │   ├── config.py
│       │   └── database.py
│       ├── models/
│       │   └── document.py
│       ├── services/
│       │   ├── document_validation_service.py
│       │   ├── extraction_service.py
│       │   ├── financial_validation_service.py
│       │   └── ocr_service.py
│       └── main.py
|
├── frontend/
│   ├── static/
│   │   ├── app.js
│   │   └── style.css
│   └── templates/
│       └── dashboard.html
|
├── tests/
│   └── test_validation.py
|
├── docs/
├── sample_outputs/
├── .env.example
├── .gitignore
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd document-intelligence-platform
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.6-luna
```

Never commit the real `.env` file or API key to GitHub.

## Running the Application

From the project root:

```bash
uvicorn backend.app.main:app --reload
```

### Frontend

```text
http://127.0.0.1:8000/
```

### Swagger / OpenAPI

```text
http://127.0.0.1:8000/docs
```

### Health Check

```text
http://127.0.0.1:8000/api/v1/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "document-intelligence-api"
}
```

## API Endpoints

### POST `/api/v1/documents/process`

Processes an uploaded financial document.

Multipart form fields:

- `file`
- `document_type`

Supported document types:

```text
invoice
balance_sheet
profit_and_loss
cash_flow_statement
```

### GET `/api/v1/documents`

Returns all processed documents.

### GET `/api/v1/documents/{document_name}`

Returns the latest stored result for a document.

### GET `/api/v1/health`

Returns the health status of the service.

## Document Validation

The upload pipeline validates:

- Supported file extension
- File readability
- Corrupted files
- Empty files
- PDF page count
- Maximum page count of 3

Supported file formats:

```text
PDF
JPG
JPEG
PNG
```

## Extraction Pipeline

The processing flow is:

```text
Upload
   |
   v
File Validation
   |
   v
Text Extraction / OCR
   |
   v
Structured AI Extraction
   |
   v
Financial Validation
   |
   v
Database Persistence
   |
   v
JSON Response
```

For PDFs, native PDF text is used when available.

For scanned or image-based documents, OCR is used.

Extracted information includes:

- Document title
- Entity name
- Currency
- Reporting periods
- Fields
- Financial line items
- Evidence snippets
- Page numbers
- Processing metadata

Missing values are represented as `null` where applicable instead of being invented.

## Financial Validation

### Invoice

The system supports checks such as:

```text
Subtotal + Tax = Total
Cash Paid - Total = Change
```

### Balance Sheet

The system validates balance-sheet components such as:

```text
Capital
+ Reserves and Surplus
+ Minority Interest
+ Deposits
+ Borrowings
+ Other Liabilities and Provisions
= Assets
```

### Profit & Loss

The system validates:

```text
Interest Earned + Other Income = Total Income
```

```text
Interest Expended
+ Operating Expenses
+ Provisions
= Total Expenditure
```

```text
Total Income - Total Expenditure
= Consolidated Net Profit Before Minority Interest
```

```text
Consolidated Profit Before Minority Interest
- Minority Interest
= Group Net Profit
```

### Cash Flow Statement

The system validates:

```text
Operating Activities
+ Investing Activities
+ Financing Activities
+ FX Effect
+ Cash Acquired on Amalgamation
= Net Increase in Cash
```

Validation results use:

```text
PASS
FAIL
NOT_APPLICABLE
```

`NOT_APPLICABLE` is returned when required operands are unavailable rather than assuming or inventing values.

## Output Format

Processed results contain:

```text
document_name
document_type
processing_status
file_validation
extracted_data
validation
processing_metadata
```

The extracted data includes evidence and page references where available.

Validation checks contain:

```text
formula
operands
calculated
reported
variance
status
```

## Database

Processed document results are persisted using SQLite and SQLAlchemy.

The database stores:

- Document name
- Document type
- Processing status
- Extracted JSON result
- OCR usage information
- Processing timestamp

## Testing

Run the automated test suite with:

```bash
pytest -q
```

The test suite covers:

- Invoice validation
- Balance Sheet validation
- Profit & Loss validation
- Cash Flow validation
- Validation failure handling

## AI / Tool Declaration

AI was used for structured extraction of financial document information from extracted text and OCR content.

The OpenAI API is used to generate structured extraction results using a typed schema.

Other technologies and tools used:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- PyMuPDF
- Tesseract OCR
- Pillow
- Jinja2
- HTML
- CSS
- JavaScript
- Pytest

## Security

- API credentials are loaded through environment variables.
- `.env` is excluded from source control.
- File validation is performed before extraction.
- Unsupported file types are rejected.
- No API key is hardcoded in source code.

## Limitations

- OCR quality depends on image resolution, document quality and layout.
- Complex tables may require additional document-specific table extraction.
- Some financial statements use different terminology, which can affect rule-based matching.
- The current implementation uses SQLite for persistence.
- Production systems should use managed database and object-storage infrastructure.
- Authentication, authorization, rate limiting and stronger audit controls would be required for a production deployment.

## Production Improvements

Potential production improvements include:

- PostgreSQL
- Cloud object storage
- Asynchronous processing queues
- Authentication and authorization
- Rate limiting
- Advanced table extraction
- Human review for low-confidence results
- Monitoring and distributed tracing
- Stronger audit logging
- Document versioning
- Role-based access control

## Sample Outputs

Representative JSON outputs are stored in:

```text
sample_outputs/
```

## Deployment

The application is deployed publicly on Render.

### Frontend

https://document-intelligence-platform-hsvm.onrender.com/

### Backend API

https://document-intelligence-platform-hsvm.onrender.com/

### Swagger / OpenAPI

https://document-intelligence-platform-hsvm.onrender.com/docs

### Health Check

https://document-intelligence-platform-hsvm.onrender.com/api/v1/health

Environment variables should be configured through the deployment platform rather than committed to the repository.

## Verification

The application has been tested with:

- Cash Flow Statement
- Balance Sheet
- Profit & Loss
- Invoice/image-based document
- Scanned/image-based OCR input
- Database persistence
- Document retrieval API
- Financial validation logic
- Automated tests

## License

This project was created as a technical assessment / internship case-study project.