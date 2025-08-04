from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import os
import io
import base64
from PIL import Image
import pdf2image
import google.generativeai as genai
import sqlite3
from typing import Optional
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="ATS Resume Analyzer API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure Google Gemini API
genai.configure(api_key="AIzaSyCGqs_KDUWBeUKQ51tz1DyXXPWzWxZpliU")

# Pydantic models
class AnalysisResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None

# Database setup
def init_db():
    conn = sqlite3.connect('ats_app.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_description TEXT,
            analysis_type TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
def input_pdf_setup(uploaded_file: bytes):
    try:
        # For Windows, specify Poppler path (update this for your setup)
        poppler_path = r"C:\Users\USER\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"
        
        # Convert PDF to images
        images = pdf2image.convert_from_bytes(uploaded_file, poppler_path=poppler_path)
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

# API Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>ATS Resume Analyzer API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .info { background: #f0f0f0; padding: 20px; border-radius: 8px; margin: 20px 0; }
                a { color: #667eea; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>🎯 ATS Resume Analyzer API</h1>
            <div class="info">
                <p><strong>API is running successfully!</strong></p>
                <p>Available endpoints:</p>
                <ul>
                    <li><a href="/docs">/docs</a> - Interactive API documentation</li>
                    <li><a href="/redoc">/redoc</a> - Alternative API documentation</li>
                    <li><a href="/health">/health</a> - Health check</li>
                </ul>
            </div>
            <div class="info">
                <h3>Quick Start:</h3>
                <p>Use POST <code>/api/analyze</code> to analyze resumes with job descriptions.</p>
                <p>Use GET <code>/api/analyses</code> to view analysis history.</p>
            </div>
        </body>
    </html>
    """

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    job_description: str = Form(...),
    analysis_type: str = Form(...),
    resume_file: UploadFile = File(...)
):
    try:
        # Validate file
        if not resume_file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Check file size
        contents = await resume_file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum 16MB allowed."
            )
        
        # Process PDF
        pdf_content = input_pdf_setup(contents)
        
        # Choose prompt based on analysis type
        if analysis_type == 'profile':
            prompt = """
            You are an experienced HR with tech experience in the fields of Data Science, Full Stack Web Development, Big Data Engineering, DEVOPS, and Data Analysis. 
            Your task is to review the provided resume against the job description for these profiles.
            Please share your professional evaluation on whether the candidate's profile aligns with the role. 
            Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
            """
        elif analysis_type == 'match':
            prompt = """
            You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality. 
            Your task is to evaluate the resume against the provided job description. 
            Give me the percentage of match if the resume matches the job description. 
            First, the output should come as a percentage, followed by missing keywords, and finally your overall thoughts.
            """
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid analysis type. Must be 'profile' or 'match'"
            )
        
        # Get AI response
        result = get_gemini_response(job_description, pdf_content, prompt)
        
        # Save analysis to database
        conn = sqlite3.connect('ats_app.db')
        c = conn.cursor()
        c.execute('INSERT INTO analyses (job_description, analysis_type, result) VALUES (?, ?, ?)',
                  (job_description, analysis_type, result))
        conn.commit()
        conn.close()
        
        return AnalysisResponse(success=True, result=result)
    
    except Exception as e:
        return AnalysisResponse(success=False, error=str(e))

@app.get("/analyses")
async def get_analyses():
    conn = sqlite3.connect('ats_app.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, job_description, analysis_type, result, created_at 
        FROM analyses 
        ORDER BY created_at DESC
        LIMIT 50
    ''')
    analyses = c.fetchall()
    conn.close()
    
    return [
        {
            "id": analysis[0],
            "job_description": analysis[1][:100] + "..." if len(analysis[1]) > 100 else analysis[1],
            "analysis_type": analysis[2],
            "result": analysis[3][:200] + "..." if len(analysis[3]) > 200 else analysis[3],
            "created_at": analysis[4]
        }
        for analysis in analyses
    ]

@app.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: int):
    conn = sqlite3.connect('ats_app.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, job_description, analysis_type, result, created_at 
        FROM analyses 
        WHERE id = ?
    ''', (analysis_id,))
    analysis = c.fetchone()
    conn.close()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return {
        "id": analysis[0],
        "job_description": analysis[1],
        "analysis_type": analysis[2],
        "result": analysis[3],
        "created_at": analysis[4]
    }

@app.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: int):
    conn = sqlite3.connect('ats_app.db')
    c = conn.cursor()
    c.execute('DELETE FROM analyses WHERE id = ?', (analysis_id,))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    conn.commit()
    conn.close()
    
    return {"message": "Analysis deleted successfully"}

@app.get("/stats")
async def get_stats():
    conn = sqlite3.connect('ats_app.db')
    c = conn.cursor()
    
    # Get total analyses count
    c.execute('SELECT COUNT(*) FROM analyses')
    total_analyses = c.fetchone()[0]
    
    # Get analyses by type
    c.execute('SELECT analysis_type, COUNT(*) FROM analyses GROUP BY analysis_type')
    analyses_by_type = dict(c.fetchall())
    
    # Get recent analyses count (last 7 days)
    c.execute('''
        SELECT COUNT(*) FROM analyses 
        WHERE created_at >= datetime('now', '-7 days')
    ''')
    recent_analyses = c.fetchone()[0]
    
    conn.close()
    
    return {
        "total_analyses": total_analyses,
        "analyses_by_type": analyses_by_type,
        "recent_analyses": recent_analyses,
        "timestamp": datetime.utcnow()
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    print("🚀 Starting ATS Resume Analyzer FastAPI Server...")
    print("📱 Server: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔧 Interactive API: http://localhost:8000/redoc")
    print("💡 Make sure to update the Poppler path in the code for PDF processing")
    print("✨ No authentication required - ready to analyze resumes!")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )