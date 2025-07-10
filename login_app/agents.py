# login_app/agents.py

import os
import warnings
from crewai import Agent, Task, Crew, Process, LLM
from langchain_groq import ChatGroq
from dotenv import load_dotenv

warnings.filterwarnings('ignore')
load_dotenv()

def get_resume_crew():
    """
    This function configures and returns the CrewAI crew for resume enhancement.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable not set. Please create a .env file and add it.")
    llm = LLM(model="groq/llama-3.3-70b-versatile",api_key= groq_api_key)

    

    # Agent 1: Resume Analyst
    resume_analyst = Agent(
        role="Senior Talent Acquisition Analyst",
        goal="To meticulously dissect a user's resume against a target job description, identify critical gaps, and produce a comprehensive strategic brief for the content and formatting teams.",
        backstory=(
            "You're the lead strategist on a resume overhaul project. Your task is to analyze the client's resume against "
            "the target job description they've provided. You meticulously identify all the key skills, keywords, and experience gaps. "
            "Your work is the essential strategic blueprint for the Content Specialist to begin the rewriting process."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True
    )

    # Agent 2: Content Specialist
    content_specialist = Agent(
        role="Master Resume Writer & Career Storyteller",
        goal="To transform the strategic brief from the Analyst into a compelling, achievement-driven narrative, expertly weaving in keywords to ensure maximum impact and ATS compatibility.",
        backstory=(
            "You're the expert wordsmith and career storyteller. You are working from the strategic blueprint "
            "provided by the Resume Analyst. Your mission is to rewrite and enrich the resume's content, "
            "infusing it with powerful action verbs and keywords to make the candidate's achievements shine. "
            "The compelling content you produce is the core material for the Formatting Expert to finalize."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True
    )

    # Agent 3: Editor
    editor = Agent(
        role="Meticulous Design & Compliance Editor",
        goal="To take the finalized content and present it in a visually appealing, professional, and perfectly polished format that is both modern and ATS-friendly, ensuring a flawless final document.",
        backstory=(
            "You're the design and quality assurance specialist. You take the masterfully written content "
            "from the Content Specialist. Your job is to ensure the final document is impeccably formatted, "
            "visually appealing, and completely free of any errors. Your meticulous work results in the final, "
            "polished resume that is ready for the client to submit with confidence."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True
    )
    
    return resume_analyst, content_specialist, editor


def run_crew(resume_text, job_description_text):
    """
    Initializes and runs the resume enhancement crew with the provided texts.
    """
    resume_analyst, content_specialist, editor = get_resume_crew()

    # Task for Agent 1: The Resume Analyst
    task_analyze_resume = Task(
        description=(
            "1. Take the user's resume and the target job description as input.\n"
            "2. Conduct a deep analysis of the job description to extract the top 5-7 most critical skills, qualifications, and keywords.\n"
            "3. Scrutinize the user's resume, comparing it against the extracted requirements.\n"
            "4. Identify specific gaps where the resume is lacking and pinpoint strengths that should be highlighted.\n"
            "5. Create a detailed 'Strategic Brief' in markdown format that lists the extracted keywords, outlines the gaps, and provides clear, actionable recommendations for content improvement.\n\n"
            "Here is the resume you need to analyze:\n"
            "--- START RESUME ---\n"
            f"{resume_text}\n"
            "--- END RESUME ---\n\n"
            "And here is the job description you need to compare it against:\n"
            "--- START JOB DESCRIPTION ---\n"
            f"{job_description_text}\n"
            "--- END JOB DESCRIPTION ---"
        ),
        expected_output=(
            "A comprehensive 'Strategic Brief' in markdown format. "
            "This brief must include a list of essential keywords, a clear gap analysis, "
            "and direct, actionable advice for the Content Specialist to use in the rewrite."
        ),
        agent=resume_analyst,
    )

    # Task for Agent 2: The Content Specialist
    task_rewrite_content = Task(
        description=(
            "1. Use the 'Strategic Brief' from the Resume Analyst as your primary guide.\n"
            "2. Rewrite the professional summary to be a powerful, concise pitch that incorporates key findings from the brief.\n"
            "3. Revise all work experience bullet points to be achievement-oriented, using strong action verbs and integrating the identified keywords and metrics.\n"
            "4. Restructure and optimize the skills section to align perfectly with the target job.\n"
            "5. Ensure the tone is professional and confident throughout the entire document."
        ),
        expected_output=(
            "A single text document containing the fully rewritten resume content. "
            "This document should have a new summary, updated experience sections, "
            "and a refined skills list, all optimized for both ATS and human readers. "
            "The content must be finalized and ready for formatting."
        ),
        agent=content_specialist,
        context=[task_analyze_resume],
    )

    # Task for Agent 3: The Editor
    task_format_resume = Task(
        description=(
            "1. Take the rewritten resume content from the Content Specialist.\n"
            "2. Meticulously format the entire content into a clean, professional, and universally ATS-friendly layout.\n"
            "3. Ensure perfect alignment, consistent fonts (like Arial or Calibri), and excellent readability with proper use of white space.\n"
            "4. Conduct a final, comprehensive proofread to eliminate any and all spelling or grammatical errors."
        ),
        expected_output=(
            "The final, fully formatted resume as a single string of text. "
            "The layout should be clean and professional, ready for a user to copy and paste into a document to save as a PDF. "
            "Do not add any conversational text, just the resume content itself."
        ),
        agent=editor,
        context=[task_rewrite_content],
    )

    resume_crew = Crew(
        agents=[resume_analyst, content_specialist, editor],
        tasks=[task_analyze_resume, task_rewrite_content, task_format_resume],
        process=Process.sequential,
        verbose=True
    )

    final_result = resume_crew.kickoff()
    return str(final_result)
