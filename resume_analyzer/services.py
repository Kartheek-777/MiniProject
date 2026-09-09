import re
import pymupdf  # PyMuPDF

# Technical Engineering Skills Vocabulary
SKILLS_VOCABULARY = [
    "Python", "Java", "C", "C++", "C#", "JavaScript", "TypeScript", "HTML", "CSS", "Bootstrap",
    "React", "React.js", "Node.js", "Express.js", "Django", "Flask", "FastAPI", "SQL", "MySQL",
    "PostgreSQL", "MongoDB", "SQLite", "Redis", "REST API", "GraphQL", "Git", "GitHub", "GitLab",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Linux", "Unix", "Bash", "Shell",
    "Data Structures", "Algorithms", "Object Oriented Programming", "OOP", "DBMS",
    "Operating Systems", "Computer Networks", "System Design", "Machine Learning",
    "Deep Learning", "Artificial Intelligence", "NLP", "Pandas", "NumPy", "Scikit-Learn",
    "TensorFlow", "PyTorch", "OpenCV", "Agile", "Scrum", "Jira", "Unit Testing"
]

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts plain text from a PDF file using PyMuPDF.
    Handles corrupted files or empty documents gracefully.
    """
    text_content = []
    try:
        doc = pymupdf.open(file_path)
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text_content.append(page_text)
        doc.close()
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"
    
    return "\n".join(text_content).strip()


def parse_resume_data(text: str) -> dict:
    """
    Applies rule-based heuristic parsing on extracted resume text to extract:
    - Email address
    - Technical skills
    - Education entries
    - Project entries
    """
    if not text:
        return {
            'email': None,
            'skills': [],
            'education': [],
            'projects': []
        }

    # 1. Email Extraction using Regex
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    extracted_email = emails[0] if emails else None

    # 2. Skills Extraction (Keyword Matching)
    found_skills = set()
    text_lower = text.lower()
    for skill in SKILLS_VOCABULARY:
        # Match exact word boundaries for short acronyms like C, C++, OOP, AWS, etc.
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)

    # 3. Education Extraction (Section & Keyword Analysis)
    education_lines = []
    edu_keywords = ['b.tech', 'b.e.', 'm.tech', 'bachelor', 'master', 'cgpa', 'gpa', 'university', 'institute', 'college', 'degree']
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    in_edu_section = False
    for line in lines:
        line_lower = line.lower()
        if 'education' in line_lower or 'academic background' in line_lower or 'qualification' in line_lower:
            in_edu_section = True
            continue
        
        # Stop section if reaching next major heading
        if in_edu_section and any(header in line_lower for header in ['projects', 'skills', 'experience', 'certifications', 'achievements']):
            in_edu_section = False

        if in_edu_section or any(kw in line_lower for kw in edu_keywords):
            if line not in education_lines and len(line) < 150:
                education_lines.append(line)

    # 4. Projects Extraction (Section Analysis)
    project_lines = []
    in_project_section = False
    for line in lines:
        line_lower = line.lower()
        if 'project' in line_lower and len(line) < 40:
            in_project_section = True
            continue
        
        if in_project_section and any(header in line_lower for header in ['education', 'skills', 'experience', 'certifications', 'achievements', 'declaration']):
            in_project_section = False

        if in_project_section:
            if line not in project_lines:
                project_lines.append(line)

    return {
        'email': extracted_email,
        'skills': sorted(list(found_skills)),
        'education': education_lines[:6],  # Limit top relevant entries
        'projects': project_lines[:10]
    }
