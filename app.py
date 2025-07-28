from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import io
import base64
from PIL import Image
import pdf2image
import google.generativeai as genai
from datetime import datetime
import sqlite3
import secrets

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Google Gemini API
genai.configure(api_key="AIzaSyCGqs_KDUWBeUKQ51tz1DyXXPWzWxZpliU")

# Database setup
def init_db():
    conn = sqlite3.connect('ats_app.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_description TEXT,
            analysis_type TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Function to get Google Gemini response
def get_gemini_response(input_text, pdf_content, prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([input_text, pdf_content[0], prompt])
        return response.text
    except Exception as e:
        return f"Error in generating response: {str(e)}"

# Function to process uploaded PDF
def input_pdf_setup(uploaded_file):
    try:
        # For Windows, specify Poppler path (update this for your setup)
        poppler_path = r"C:\Users\USER\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"
        
        # Convert PDF to images
        images = pdf2image.convert_from_bytes(uploaded_file.read(), poppler_path=poppler_path)
        first_page = images[0]

        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode(),
            }
        ]
        return pdf_parts
    except Exception as e:
        raise RuntimeError(f"Error processing PDF: {str(e)}")

# HTML Templates
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATS Resume Analyzer - Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-container {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 400px;
            backdrop-filter: blur(10px);
        }
        
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .logo h1 {
            color: #333;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .logo p {
            color: #666;
            font-size: 0.9rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .switch-form {
            text-align: center;
            margin-top: 1.5rem;
            color: #666;
        }
        
        .switch-form a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        
        .switch-form a:hover {
            text-decoration: underline;
        }
        
        .alert {
            padding: 0.75rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            border-left: 4px solid #e74c3c;
            background-color: #fdf2f2;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🎯 ATS Analyzer</h1>
            <p>Resume Analysis & Job Matching</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn">Sign In</button>
        </form>
        
        <div class="switch-form">
            Don't have an account? <a href="{{ url_for('signup') }}">Sign up here</a>
        </div>
    </div>
</body>
</html>
'''

SIGNUP_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATS Resume Analyzer - Sign Up</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .signup-container {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 400px;
            backdrop-filter: blur(10px);
        }
        
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .logo h1 {
            color: #333;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .logo p {
            color: #666;
            font-size: 0.9rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .switch-form {
            text-align: center;
            margin-top: 1.5rem;
            color: #666;
        }
        
        .switch-form a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        
        .switch-form a:hover {
            text-decoration: underline;
        }
        
        .alert {
            padding: 0.75rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            border-left: 4px solid #e74c3c;
            background-color: #fdf2f2;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="signup-container">
        <div class="logo">
            <h1>🎯 ATS Analyzer</h1>
            <p>Create Your Account</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <div class="form-group">
                <label for="confirm_password">Confirm Password</label>
                <input type="password" id="confirm_password" name="confirm_password" required>
            </div>
            
            <button type="submit" class="btn">Create Account</button>
        </form>
        
        <div class="switch-form">
            Already have an account? <a href="{{ url_for('login') }}">Sign in here</a>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATS Resume Analyzer - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f8f9ff;
            min-height: 100vh;
        }
        
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 0;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo h1 {
            font-size: 1.5rem;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            font-weight: 500;
            transition: opacity 0.3s ease;
        }
        
        .nav-links a:hover {
            opacity: 0.8;
        }
        
        .main-container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        
        .welcome-section {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            margin-bottom: 2rem;
        }
        
        .welcome-section h2 {
            color: #333;
            margin-bottom: 0.5rem;
        }
        
        .welcome-section p {
            color: #666;
        }
        
        .analysis-section {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            margin-bottom: 2rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 600;
        }
        
        .form-group textarea {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            font-family: inherit;
            resize: vertical;
            min-height: 120px;
            transition: border-color 0.3s ease;
        }
        
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .file-upload {
            position: relative;
            display: inline-block;
            width: 100%;
        }
        
        .file-upload input[type="file"] {
            display: none;
        }
        
        .file-upload-btn {
            display: block;
            width: 100%;
            padding: 1rem;
            background: #f8f9ff;
            border: 2px dashed #667eea;
            border-radius: 8px;
            text-align: center;
            color: #667eea;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .file-upload-btn:hover {
            background: #667eea;
            color: white;
        }
        
        .file-selected {
            margin-top: 0.5rem;
            color: #28a745;
            font-weight: 500;
        }
        
        .button-group {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .btn {
            flex: 1;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .result-section {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            margin-top: 2rem;
            display: none;
        }
        
        .result-section h3 {
            color: #333;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .result-content {
            background: #f8f9ff;
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #667eea;
        }
        
        .loading::after {
            content: '';
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .alert {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            border-left: 4px solid #e74c3c;
            background-color: #fdf2f2;
            color: #721c24;
        }
        
        .alert.success {
            border-left-color: #28a745;
            background-color: #f2fdf4;
            color: #1e4d23;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <h1>🎯 ATS Resume Analyzer</h1>
            </div>
            <div class="nav-links">
                <span>Welcome, {{ session.username }}!</span>
                <a href="{{ url_for('logout') }}">Logout</a>
            </div>
        </div>
    </nav>
    
    <div class="main-container">
        <div class="welcome-section">
            <h2>Resume Analysis Dashboard</h2>
            <p>Upload your resume and job description to get AI-powered insights and match percentage analysis.</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert {{ 'success' if category == 'success' else '' }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="analysis-section">
            <form id="analysisForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="jobDescription">Job Description</label>
                    <textarea id="jobDescription" name="job_description" placeholder="Paste the job description here..." required></textarea>
                </div>
                
                <div class="form-group">
                    <label>Upload Resume (PDF)</label>
                    <div class="file-upload">
                        <input type="file" id="resumeFile" name="resume_file" accept=".pdf" required>
                        <label for="resumeFile" class="file-upload-btn">
                            📄 Click to upload your resume (PDF only)
                        </label>
                        <div id="fileSelected" class="file-selected" style="display: none;"></div>
                    </div>
                </div>
                
                <div class="button-group">
                    <button type="button" class="btn btn-primary" onclick="analyzeResume('profile')">
                        📋 Analyze Resume Profile
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="analyzeResume('match')">
                        📊 Get Match Percentage
                    </button>
                </div>
            </form>
        </div>
        
        <div id="resultSection" class="result-section">
            <h3 id="resultTitle">Analysis Result</h3>
            <div id="resultContent" class="result-content"></div>
        </div>
    </div>
    
    <script>
        // File upload handling
        document.getElementById('resumeFile').addEventListener('change', function(e) {
            const fileSelected = document.getElementById('fileSelected');
            if (e.target.files.length > 0) {
                fileSelected.textContent = `✅ Selected: ${e.target.files[0].name}`;
                fileSelected.style.display = 'block';
            } else {
                fileSelected.style.display = 'none';
            }
        });
        
        // Analysis function
        function analyzeResume(analysisType) {
            const form = document.getElementById('analysisForm');
            const formData = new FormData(form);
            const resultSection = document.getElementById('resultSection');
            const resultContent = document.getElementById('resultContent');
            const resultTitle = document.getElementById('resultTitle');
            
            // Validate form
            if (!formData.get('job_description').trim()) {
                alert('Please enter a job description');
                return;
            }
            
            if (!formData.get('resume_file')) {
                alert('Please upload a resume file');
                return;
            }
            
            // Show loading
            resultSection.style.display = 'block';
            resultTitle.textContent = analysisType === 'profile' ? '📋 Resume Profile Analysis' : '📊 Match Percentage Analysis';
            resultContent.className = 'loading';
            resultContent.textContent = 'Analyzing your resume... This may take a few moments';
            
            // Add analysis type to form data
            formData.append('analysis_type', analysisType);
            
            // Send request
            fetch('/analyze', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                resultContent.className = 'result-content';
                if (data.success) {
                    resultContent.textContent = data.result;
                } else {
                    resultContent.textContent = `Error: ${data.error}`;
                }
            })
            .catch(error => {
                resultContent.className = 'result-content';
                resultContent.textContent = `Error: ${error.message}`;
            });
        }
    </script>
</body>
</html>
'''

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('ats_app.db')
        c = conn.cursor()
        c.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template_string(SIGNUP_TEMPLATE)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long')
            return render_template_string(SIGNUP_TEMPLATE)
        
        conn = sqlite3.connect('ats_app.db')
        c = conn.cursor()
        
        # Check if username or email already exists
        c.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if c.fetchone():
            flash('Username or email already exists')
            conn.close()
            return render_template_string(SIGNUP_TEMPLATE)
        
        # Create new user
        password_hash = generate_password_hash(password)
        c.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                  (username, email, password_hash))
        conn.commit()
        conn.close()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template_string(SIGNUP_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template_string(DASHBOARD_TEMPLATE, session=session)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        job_description = request.form['job_description']
        analysis_type = request.form['analysis_type']
        uploaded_file = request.files['resume_file']
        
        if not uploaded_file or uploaded_file.filename == '':
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        if not uploaded_file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files are allowed'})
        
        # Process PDF
        pdf_content = input_pdf_setup(uploaded_file)
        
        # Choose prompt based on analysis type
        if analysis_type == 'profile':
            prompt = """
            You are an experienced HR with tech experience in the fields of Data Science, Full Stack Web Development, Big Data Engineering, DEVOPS, and Data Analysis. 
            Your task is to review the provided resume against the job description for these profiles.
            Please share your professional evaluation on whether the candidate's profile aligns with the role. 
            Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
            """
        else:  # match
            prompt = """
            You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality. 
            Your task is to evaluate the resume against the provided job description. 
            Give me the percentage of match if the resume matches the job description. 
            First, the output should come as a percentage, followed by missing keywords, and finally your overall thoughts.
            """
        
        # Get AI response
        result = get_gemini_response(job_description, pdf_content, prompt)
        
        # Save analysis to database
        conn = sqlite3.connect('ats_app.db')
        c = conn.cursor()
        c.execute('INSERT INTO analyses (user_id, job_description, analysis_type, result) VALUES (?, ?, ?, ?)',
                  (session['user_id'], job_description, analysis_type, result))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("🚀 Starting ATS Resume Analyzer Web App...")
    print("📱 Access the app at: http://localhost:5000")
    print("💡 Make sure to update the Poppler path in the code for PDF processing")
    app.run(debug=True, host='0.0.0.0', port=5000)