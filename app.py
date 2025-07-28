"""
MailMorph - Email Domain Replacer Tool
Main Flask Application
"""

import os
import uuid
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'csv,txt').split(','))
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB
MAX_ROWS_LIMIT = int(os.getenv('MAX_ROWS_LIMIT', 100000))

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_domain(domain):
    """Validate domain format"""
    if not domain:
        return False
    
    # Basic domain validation regex
    domain_regex = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(domain_regex, domain)) and len(domain) <= 253

def process_csv_file(filepath, old_domain, new_domain):
    """Process CSV file and replace email domains"""
    try:
        # Read CSV file
        df = pd.read_csv(filepath)
        
        if df.empty:
            return {'success': False, 'error': 'CSV file is empty'}
        
        if len(df) > MAX_ROWS_LIMIT:
            return {'success': False, 'error': f'File exceeds maximum row limit of {MAX_ROWS_LIMIT:,}'}
        
        changes_made = 0
        email_pattern = rf'([a-zA-Z0-9._%+-]+)@{re.escape(old_domain)}'
        replacement = rf'\\1@{new_domain}'
        
        # Process each column
        for col in df.columns:
            if df[col].dtype == 'object':  # Only process string columns
                original_values = df[col].astype(str)
                updated_values = original_values.str.replace(
                    email_pattern, replacement, regex=True, case=False
                )
                
                # Count changes in this column
                changes_in_col = (original_values != updated_values).sum()
                changes_made += changes_in_col
                
                # Update the column
                df[col] = updated_values
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'mailmorph_output_{timestamp}.csv'
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        # Save processed file
        df.to_csv(output_path, index=False)
        
        return {
            'success': True,
            'output_file': output_filename,
            'changes_made': changes_made,
            'total_rows': len(df),
            'old_domain': old_domain,
            'new_domain': new_domain
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Error processing file: {str(e)}'}

@app.route('/')
def index():
    """Main upload page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and domain replacement"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        file = request.files['file']
        old_domain = request.form.get('old_domain', '').strip()
        new_domain = request.form.get('new_domain', '').strip()
        
        # Validate inputs
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        if not old_domain or not new_domain:
            flash('Both old and new domains are required', 'error')
            return redirect(url_for('index'))
        
        if not validate_domain(old_domain) or not validate_domain(new_domain):
            flash('Invalid domain format', 'error')
            return redirect(url_for('index'))
        
        if old_domain.lower() == new_domain.lower():
            flash('Old and new domains cannot be the same', 'error')
            return redirect(url_for('index'))
        
        # Check file extension
        if not allowed_file(file.filename):
            flash('Invalid file type. Only CSV and TXT files are allowed.', 'error')
            return redirect(url_for('index'))
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Process the file
        result = process_csv_file(filepath, old_domain, new_domain)
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass
        
        if result['success']:
            return render_template('result.html', result=result)
        else:
            flash(result['error'], 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download processed file"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            flash('File not found or has expired', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/validate', methods=['POST'])
def validate_domains():
    """API endpoint for domain validation"""
    data = request.get_json()
    old_domain = data.get('old_domain', '').strip()
    new_domain = data.get('new_domain', '').strip()
    
    return jsonify({
        'old_domain_valid': validate_domain(old_domain),
        'new_domain_valid': validate_domain(new_domain),
        'domains_different': old_domain.lower() != new_domain.lower() if old_domain and new_domain else True
    })

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    flash('An internal server error occurred. Please try again.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)