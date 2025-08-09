# section.py (updated to be a module with functions)

from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv

load_dotenv() # Load environment variables, including GROQ_API_KEY if used here

def get_headings_from_pdf(pdf_file_path):
    """
    Extracts headings from a PDF document.
    Returns a tuple: (list of headings, full content of the PDF).
    """
    llm = ChatGroq(model="meta-llama/llama-4-maverick-17b-128e-instruct")
    parser = StrOutputParser()

    loader = PyPDFLoader(pdf_file_path)
    document = loader.load()
    
    if not document:
        return [], ""

    doc_content = document[0].page_content

    prompt = PromptTemplate(
        template=(
            "Analyze the entire PDF document text below:\n\n"
            "{text}\n\n"
            "Return only the **headings** present in the document, "
            "excluding the applicant's name. Format them as a comma-separated list, e.g., 'Summary, Experience, Education'."
        ),
        input_variables=["text"]
    )
    chain = prompt | llm | parser
    headings_raw = chain.invoke({"text": doc_content})
    headings = [h.strip().replace('*', '') for h in headings_raw.split(',') if h.strip()]
    return headings, doc_content

def get_enhanced_section(full_resume_content, selected_heading):
    """
    Enhances a specific section of the resume.
    Returns the enhanced section text.
    """
    llm = ChatGroq(model="meta-llama/llama-4-maverick-17b-128e-instruct")
    parser = StrOutputParser()

    prompt1 = PromptTemplate(
        template=(
            "You are an expert resume editor. The resume content is given below:\n\n"
            "{content}\n\n"
            "The user wants to enhance only the **{text}** section of the resume.\n"
            "Your task:\n"
            "- Rewrite only the {text} section to make it more professional, concise, and well-structured.\n"
            "- Do NOT include any other part of the resume.\n"
            "- Do NOT explain your edits or list what you changed.\n"
            "- ONLY return the updated version of the {text} section as plain text.\n\n"
            "Begin:"
        ),
        input_variables=["content", "text"]
    )
    chain1 = prompt1 | llm | parser
    enhanced_result = chain1.invoke({"content": full_resume_content, "text": selected_heading})
    return enhanced_result