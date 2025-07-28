# 🎯 ATS Resume Analyzer Web Application

A modern, full-stack web application that analyzes resumes against job descriptions using AI-powered insights. Built with Flask, featuring user authentication, file upload, and real-time analysis using Google Gemini AI.

![ATS Resume Analyzer](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### 🔐 User Authentication
- Secure signup/login system
- Password hashing with Werkzeug
- Session management
- User profile dashboard

### 📄 Resume Analysis
- **Profile Analysis**: Detailed evaluation of candidate profile against job requirements
- **Match Percentage**: ATS-style scoring with missing keywords identification
- **PDF Processing**: Converts PDF resumes to images for AI analysis
- **History Tracking**: Saves all analyses to user database

### 🎨 Modern UI/UX
- Responsive design that works on all devices
- Beautiful gradient backgrounds and animations
- Interactive file upload with drag-and-drop support
- Real-time loading indicators
- Professional dashboard layout

### 🔒 Security Features
- CSRF protection
- File type validation (PDF only)
- File size limits (16MB max)
- SQL injection protection
- Secure password requirements

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Internet connection for package installation
- Google Gemini API key

### Option 1: Automated Setup (Recommended)
```bash
# Download the setup script and run it
python setup.py
```

### Option 2: Manual Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Poppler (Required for PDF processing)**
   
   **Windows:**
   - Download from: https://github.com/oschwartz10612/poppler-windows/releases/
   - Extract to `C:\poppler`
   - Update `poppler_path` in `app.py`
   
   **Linux:**
   ```bash
   sudo apt-get install poppler-utils
   ```
   
   **macOS:**
   ```bash
   brew install poppler
   ```

3. **Configure Google Gemini API**
   - Get your API key from: https://makersuite.google.com/app/apikey
   - Replace the API key in `app.py` or create a `.env` file:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the App**
   - Open your browser to: http://localhost:5000

## 📁 Project Structure

```
ats-web-app/
├── app.py                 # Main Flask application
├── setup.py              # Automated setup script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env                  # Environment variables (created during setup)
├── ats_app.db           # SQLite database (auto-created)
└── uploads/             # File upload directory (auto-created)
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
GOOGLE_API_KEY=your_gemini_api_key
FLASK_SECRET_KEY=your_secret_key
FLASK_DEBUG=True
DATABASE_URL=sqlite:///ats_app.db
MAX_FILE_SIZE=16777216
UPLOAD_FOLDER=uploads
POPPLER_PATH=C:\poppler\Library\bin  # Windows only
```

### Database Schema
The application uses SQLite with two main tables:
- `users`: User authentication and profile data
- `analyses`: Resume analysis history and results

## 🎯 How to Use

1. **Sign Up**: Create a new account with username, email, and password
2. **Login**: Access your personal dashboard
3. **Upload Resume**: Select a PDF file of your resume
4. **Enter Job Description**: Paste the job posting you're applying for
5. **Choose Analysis Type**:
   - **Profile Analysis**: Get detailed feedback on your resume
   - **Match Percentage**: See how well your resume matches the job
6. **View Results**: Get AI-powered insights and recommendations

## 🤖 AI Analysis Types

### Profile Analysis
- Comprehensive evaluation by an experienced HR perspective
- Strengths and weaknesses identification
- Alignment assessment with job requirements
- Professional recommendations for improvement

### Match Percentage Analysis
- ATS-style compatibility scoring
- Missing keywords identification
- Overall match percentage
- Specific recommendations for optimization

## 🛠️ Customization

### Adding New Analysis Types
1. Create new prompts in the `analyze()` route
2. Add corresponding buttons in the dashboard template
3. Update the JavaScript `analyzeResume()` function

### Changing AI Models
The application currently uses Google Gemini, but you can easily switch to:
- OpenAI GPT models
- Anthropic Claude
- Local models via Ollama
- Any other text generation API

### UI Customization
- Modify CSS gradients and colors in the HTML templates
- Add new sections to the dashboard
- Customize the color scheme and branding

## 🐛 Troubleshooting

### Common Issues

**Poppler Error**: "Unable to get page count"
- Ensure Poppler is installed and path is correct
- Check file permissions and system PATH

**API Error**: "Invalid API key"
- Verify your Google Gemini API key is correct
- Check API quota and billing status

**PDF Processing Error**: "Error processing PDF"
- Ensure uploaded file is a valid PDF
- Check file size (must be under 16MB)
- Try with a different PDF file

**Database Error**: "Database locked"
- Restart the application
- Check file permissions on ats_app.db

## 🚢 Deployment

### Local Development
```bash
python app.py
```

### Production Options
- **Heroku**: Web hosting platform
- **Railway**: Modern app deployment
- **DigitalOcean**: App platform
- **AWS**: Elastic Beanstalk
- **Google Cloud**: Cloud Run

### Production Checklist
- [ ] Set environment variables for sensitive data
- [ ] Enable HTTPS
- [ ] Configure database connection pooling
- [ ] Set up cloud file storage (AWS S3, Google Cloud Storage)
- [ ] Implement rate limiting
- [ ] Add logging and monitoring
- [ ] Update security headers

## 📊 Technical Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (can be upgraded to PostgreSQL)
- **AI**: Google Gemini Pro
- **PDF Processing**: pdf2image + Poppler
- **Authentication**: Werkzeug security
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with modern gradients

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powerful text analysis
- Poppler developers for PDF processing
- Flask community for the excellent web framework
- pdf2image library for seamless PDF to image conversion

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the setup instructions
3. Ensure all dependencies are properly installed
4. Verify your API keys and configuration

## 🔮 Future Enhancements

- [ ] Multiple file format support (DOC, DOCX)
- [ ] Batch resume processing
- [ ] Advanced analytics dashboard
- [ ] Email notifications for analysis completion
- [ ] Resume template suggestions
- [ ] Integration with job boards APIs
- [ ] Mobile app development
- [ ] Advanced reporting and insights

---

**Made with ❤️ by [Your Name]**

*Transform your job search with AI-powered resume analysis!*
