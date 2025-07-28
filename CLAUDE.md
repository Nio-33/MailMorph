# MailMorph - Email Domain Replacer Tool

## Overview
MailMorph is a Flask-based web application that transforms email domains in CSV files. It allows users to upload CSV files containing email addresses and replace old domains with new ones in bulk - perfect for company migrations, rebranding, or email list management.

## Quick Start

### Prerequisites
- Python 3.8+
- 2GB RAM minimum
- 1GB free disk space

### Installation
```bash
# Clone or navigate to project directory
cd MailMorph

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
```

### Running the Application
```bash
# Development mode
python run.py

# Or using Flask directly
flask run

# Access at: http://localhost:5000
```

## Usage

### Step 1: Prepare Your CSV File
Your CSV file should contain email addresses in any column. Example:
```csv
Name,Email,Department
John Doe,john.doe@oldcompany.com,Engineering
Jane Smith,jane.smith@oldcompany.com,Marketing
```

### Step 2: Transform Domains
1. Open http://localhost:5000 in your browser
2. Upload your CSV file (drag & drop or browse)
3. Enter old domain: `oldcompany.com`
4. Enter new domain: `newcompany.com`
5. Click "Transform Domains"
6. Download the updated CSV file

### Example Transformation
**Input:**
```csv
Name,Email,Department
John Doe,john.doe@techcorp.com,Engineering
Jane Smith,jane.smith@techcorp.com,Marketing
```

**After transforming `techcorp.com` → `innovatetech.com`:**
```csv
Name,Email,Department
John Doe,john.doe@innovatetech.com,Engineering
Jane Smith,jane.smith@innovatetech.com,Marketing
```

## Features

### Core Functionality
- ✅ **Bulk Domain Replacement**: Transform thousands of email addresses in seconds
- ✅ **Smart Detection**: Automatically finds and replaces email domains in any CSV column
- ✅ **File Validation**: Validates CSV structure and content before processing
- ✅ **Secure Upload**: File type validation and size limits (16MB max)
- ✅ **Auto Cleanup**: Files automatically deleted after 30 minutes

### User Interface
- ✅ **Drag & Drop Upload**: Intuitive file upload interface
- ✅ **Real-time Validation**: Domain format validation as you type
- ✅ **Responsive Design**: Works on desktop, tablet, and mobile
- ✅ **Progress Indicators**: Loading states and processing feedback
- ✅ **Professional Styling**: Clean, modern Bootstrap-based UI

### Security Features
- ✅ **Input Sanitization**: All user inputs validated and sanitized
- ✅ **File Type Restrictions**: Only CSV and TXT files allowed
- ✅ **Size Limits**: Configurable file size restrictions
- ✅ **Secure Filenames**: Auto-generated secure filenames
- ✅ **Temporary Storage**: Files processed in isolated directories

## Configuration

### Environment Variables (.env)
```bash
# Application Settings
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-super-secret-key-here

# File Upload Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
ALLOWED_EXTENSIONS=csv,txt

# File Management
CLEANUP_INTERVAL=3600        # Clean files every hour
MAX_FILE_AGE=1800           # Delete files after 30 minutes
MAX_ROWS_LIMIT=100000       # Maximum rows per CSV

# Security
DOMAIN_VALIDATION_ENABLED=True
```

### File Limits
- **Maximum file size**: 16MB (configurable)
- **Supported formats**: CSV, TXT
- **Maximum rows**: 100,000 (configurable)
- **File retention**: 30 minutes (configurable)

## Project Structure
```
mailmorph/
├── app.py                   # Main Flask application
├── config.py               # Configuration management
├── run.py                  # Development server launcher
├── wsgi.py                 # Production WSGI entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
│
├── src/
│   ├── processors/
│   │   ├── domain_replacer.py  # Core domain replacement logic
│   │   └── csv_validator.py    # CSV file validation
│   └── utils/
│       ├── file_handler.py     # File operations and cleanup
│       └── security.py         # Security utilities
│
├── templates/
│   ├── base.html              # Base template
│   ├── index.html            # Main upload page
│   └── result.html           # Download results page
│
├── static/
│   ├── css/main.css          # Custom styles
│   ├── js/main.js            # JavaScript functionality
│   └── images/               # Static images
│
├── uploads/                  # Temporary file storage (auto-created)
└── tests/                    # Unit tests
```

## API Endpoints

### Web Routes
- `GET /` - Main upload page
- `POST /upload` - Process file upload and domain replacement
- `GET /download/<filename>` - Download processed file

### API Routes
- `POST /api/validate` - Validate domain formats (AJAX)

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=src tests/
```

### Development Mode
```bash
# Run with auto-reload
python run.py

# Or with Flask CLI
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

## Deployment

### Production Setup
```bash
# Set production environment
export FLASK_ENV=production
export FLASK_DEBUG=False

# Generate secure secret key
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

### Docker Deployment
```bash
# Build image
docker build -t mailmorph .

# Run container
docker run -p 5000:5000 mailmorph
```

### Environment Variables for Production
```bash
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-production-secret-key
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=16777216
```

## Troubleshooting

### Common Issues

**"No file selected" error**
- Ensure you've selected a CSV or TXT file
- Check file size is under 16MB limit

**"Invalid file format" error**
- Verify file is properly formatted CSV
- Check for correct CSV structure with headers

**"Domain not found" error**
- Verify the old domain exists in your CSV file
- Check for typos in domain names
- Ensure domains don't include @ symbol

**Server won't start**
- Check Python version (3.8+ required)
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Verify .env file exists and is configured

### Debug Mode
Enable debug mode for detailed error messages:
```bash
export FLASK_DEBUG=True
python run.py
```

### Logs
Application logs include:
- File upload events
- Processing statistics
- Error details
- Security events

## Security Considerations

### Input Validation
- All file uploads validated for type and size
- Domain names validated against regex patterns
- User inputs sanitized before processing

### File Security
- Secure filename generation
- Temporary file storage with auto-cleanup
- File content validation for suspicious patterns

### Network Security
- CSRF protection (can be enabled)
- Rate limiting (configurable)
- Secure headers (configurable)

## Performance

### Optimization Tips
- Use virtual environment for isolation
- Enable file cleanup to manage disk space
- Monitor memory usage with large CSV files
- Consider chunked processing for very large files

### Monitoring
- File processing statistics
- Upload/download metrics
- Error rates and types
- Resource usage

## Support

### Getting Help
- Check this documentation first
- Review error messages carefully
- Enable debug mode for detailed logs
- Check file format and size requirements

### Reporting Issues
When reporting issues, include:
- Error message details
- File size and format
- Browser and OS information
- Steps to reproduce

## License
MIT License - See LICENSE file for details

## Claude's Memories

### Project Interactions
- Assisted in understanding MailMorph's architecture and functionality
- Provided guidance on project structure and best practices
- Helped clarify security considerations and performance optimization strategies