# login_app/ats_service.py

# This file contains the core logic for the ATS functionality,
# extracted from the original Streamlit application.
# It uses PyMuPDF for PDF text extraction and an LLM for generating responses.

import fitz  # PyMuPDF for PDF handling
import os
from dotenv import load_dotenv
from groq import Groq  # Import the Groq client

# Load environment variables from a .env file.
# Note: For production, you should manage your API keys more securely,
# for example, using Django's settings.py.
load_dotenv()

# The Groq API key should be set in your environment variables.
# For example, in a .env file: GROQ_API_KEY="your-api-key"
# You will also need to install the library: pip install groq
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def get_llm_response(prompt: str) -> str:
    """
    Calls the Groq API to get a response from an LLM.
    
    Args:
        prompt (str): The full prompt to send to the LLM.
        
    Returns:
        str: The response from the LLM.
    """
    if not GROQ_API_KEY:
        return "Error: GROQ_API_KEY not found in environment variables."
        
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-8b-8192",  # You can choose a different model if needed.
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return "Sorry, I am unable to process this request at the moment. Please check your API key and network connection."

def extract_text_from_pdf(pdf_file) -> str:
    """
    Extracts text from a PDF file uploaded via Django's request.FILES.
    
    Args:
        pdf_file: The InMemoryUploadedFile object from Django's request.FILES.
        
    Returns:
        str: The extracted text from the PDF.
        
    Raises:
        FileNotFoundError: If no file is provided.
    """
    if pdf_file:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    else:
        raise FileNotFoundError("No file uploaded")

def generate_ats_evaluation(resume_text: str, job_description: str, prompt_type: str) -> str:
    """
    Generates a response from the LLM based on the prompt type.

    Args:
        resume_text (str): The extracted text from the resume.
        job_description (str): The job description text.
        prompt_type (str): The type of prompt to use ('hr_review' or 'ats_match').

    Returns:
        str: The LLM's response.
    """
    hr_prompt = """
    You are an experienced Technical Human Resource Manager. Your task is to review the provided resume against the job description.
    Please share your professional evaluation on whether the candidate's profile aligns with the role.
    Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
    """
    
    ats_prompt = """
    You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality.
    Your task is to evaluate the resume against the provided job description.
    Give the percentage match, list keywords that are missing, and provide final thoughts.
    """
    
    final_prompt = ""
    if prompt_type == 'hr_review':
        final_prompt = hr_prompt
    elif prompt_type == 'ats_match':
        final_prompt = ats_prompt

    full_input = f"Job Description:\n{job_description}\n\nResume Text:\n{resume_text}\n\n{final_prompt}"
    
    return get_llm_response(full_input)
