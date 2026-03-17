import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from pypdf import PdfReader
from docx import Document
from groq import Groq
from pydantic import BaseModel
 
app = FastAPI(title="BRD Analyzer API")
 
 
class SprintResponse(BaseModel):
    explanation: str
    sprint_plan: str
 
 
def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text
 
 
def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs])
 
 
@app.post("/generate-sprint", response_model=SprintResponse)
async def generate_sprint(file: UploadFile = File(...)):
 
    groq_api_key = "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"
 
    client = Groq(api_key=groq_api_key)
 
    filename = file.filename.lower()
 
    if not (filename.endswith(".pdf") or filename.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX supported")
 
    file_bytes = await file.read()
 
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    else:
        text = extract_text_from_docx(file_bytes)
 
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text found")
 
    prompt = f"""
You are a professional Business Analyst.
 
You will receive BRD content.
 
Your task is to produce TWO outputs.
 
------------------------------------
 
SECTION 1: EXPLANATION
 
Explain the BRD clearly and in detail.
Explain:
 
- project goal
- system overview
- important modules
- workflows
- functional requirements
 
Write the explanation in clean paragraphs.
 
------------------------------------
 
SECTION 2: SPRINT PLAN
 
Create a professional sprint plan for developing the application.
 
Write it as structured text (NOT table).
 
Format example:
 
Sprint 1: Project Setup
 
Module:
User Story:
Tasks:
- task 1
- task 2
 
Acceptance Criteria:
- criteria 1
- criteria 2
 
Leave proper spacing between each sprint.
 
------------------------------------
 
IMPORTANT OUTPUT FORMAT
 
###EXPLANATION###
Explanation text here
 
###SPRINT###
Sprint plan text here
 
------------------------------------
 
BRD CONTENT:
 
{text}
"""
 
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an expert Agile planning assistant"},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        max_tokens=4000
    )
 
    ai_output = response.choices[0].message.content
 
    explanation = ""
    sprint_plan = ""
 
    try:
        explanation = ai_output.split("###EXPLANATION###")[1].split("###SPRINT###")[0].strip()
        sprint_plan = ai_output.split("###SPRINT###")[1].strip()
    except:
        explanation = ai_output
 
    return {
        "explanation": explanation,
        "sprint_plan": sprint_plan
    }
 
 
@app.get("/")
def root():
    return {"message": "BRD Analyzer API running"}