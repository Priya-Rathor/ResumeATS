#------------------------------------------------------------------------------------------------
# 1. Field to put my JD
# 2. Updoad PDF
# 3. PDF to  image---->processing --> Google Gemini pro
# 4. Prompts template  [multiple Prompts]
#--------------------------------------------------------------------------------------------


from dotenv import load_dotenv
import streamlit as st
import os
import io
import base64
from PIL import Image
import pdf2image
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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
    if uploaded_file is not None:
        try:
            # Specify Poppler path (update this for your setup)
            poppler_path = r"C:\Users\USER\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"  # Windows path example

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
    else:
        raise FileNotFoundError("No file uploaded")



# Streamlit App
st.set_page_config(page_title="ATS Resume Expert")
st.header("ATS Tracking System")

# Input fields
input_text = st.text_area("Job Description:", key="input")
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

if uploaded_file is not None:
    st.success("PDF uploaded successfully!")

# Buttons for various prompts
submit1 = st.button("Tell Me about the resume")
submit3 = st.button("Percentage match")

# Input prompts
input_prompt1 = """
You are an experienced HR with tech experience in the fields of Data Science, Full Stack Web Development, Big Data Engineering, DEVOPS, and Data Analysis. 
Your task is to review the provided resume against the job description for these profiles.
Please share your professional evaluation on whether the candidate's profile aligns with the role. 
Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
"""

input_prompt3 = """
You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality. 
Your task is to evaluate the resume against the provided job description. 
Give me the percentage of match if the resume matches the job description. 
First, the output should come as a percentage, followed by missing keywords, and finally your overall thoughts.
"""

# Process input and display results
if submit1:
    if uploaded_file is not None:
        try:
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt1)
            st.subheader("Response:")
            st.write(response)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please upload a resume.")

elif submit3:
    if uploaded_file is not None:
        try:
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt3)
            st.subheader("Response:")
            st.write(response)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please upload a resume.")
