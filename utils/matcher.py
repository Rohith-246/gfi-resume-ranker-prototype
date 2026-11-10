import re
import datetime
import os

try:
    from google import genai
    from google.genai import types

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def parse_experience_dates(text: str) -> float:
    """Calculates professional experience years from date ranges or mentions."""
    current_year = datetime.datetime.now().year
    years_found = []

    date_ranges = re.findall(r'(20\d{2})\s*[-–to]+\s*(20\d{2}|present|current)', text, re.IGNORECASE)
    for start, end in date_ranges:
        start_yr = int(start)
        end_yr = current_year if end.lower() in ['present', 'current'] else int(end)
        if 1990 <= start_yr <= current_year and start_yr <= end_yr:
            years_found.append(end_yr - start_yr)

    if years_found:
        return float(max(years_found))

    exp_matches = re.findall(r'(\d+[\.\d]*)\+?\s*(?:years?|yrs?)', text, re.IGNORECASE)
    if exp_matches:
        try:
            val = float(max(exp_matches, key=lambda x: float(x)))
            return val if val <= 30 else 2.0
        except:
            pass

    return 2.0 if ("senior" in text.lower() or "lead" in text.lower() or "manager" in text.lower()) else 1.0


def evaluate_resume(resume_text: str, jd1_text: str, jd2_text: str, weights=(0.4, 0.3, 0.2, 0.1)) -> dict:
    """
    Hybrid Enterprise Scoring Engine: Combines high-speed heuristic keyword/tenure
    analysis with optional Gemini LLM semantic reasoning for maximum accuracy.
    """
    try:
        if not resume_text or "Error" in resume_text:
            return {
                "candidate_name": "Unreadable Document",
                "email": "N/A",
                "phone": "N/A",
                "key_skills": [],
                "estimated_years_experience": 0.0,
                "lca_match_score": 0,
                "lca_reasoning": "Extraction failed.",
                "uiux_match_score": 0,
                "uiux_reasoning": "Extraction failed.",
                "recommended_role": "Uncertain",
                "reviewer_status": "Pending",
                "reviewer_notes": ""
            }

        # 1. Candidate Name Extraction
        lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
        candidate_name = "Candidate (Anonymized)"
        for line in lines[:5]:
            if any(w in line.lower() for w in ['resume', 'curriculum', 'cv', 'page', 'email', 'phone']):
                continue
            if len(line.split()) <= 4 and not any(char.isdigit() for char in line) and "@" not in line:
                candidate_name = line
                break

        # 2. Contact Information Extraction
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resume_text)
        phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', resume_text)
        email = email_match.group(0) if email_match else "Not Provided"
        phone = phone_match.group(0) if phone_match else "Not Provided"

        # 3. Experience & Skills Parsing
        years = parse_experience_dates(resume_text)

        skill_pool = [
            "Python", "Figma", "UI/UX", "User Research", "Wireframing", "Prototyping",
            "Life Cycle Assessment", "LCA", "Carbon Footprint", "Sustainability",
            "Environmental Impact", "Data Analysis", "Reporting", "SQL", "Excel", "React",
            "Framer", "Adobe XD", "User Testing", "Carbon Accounting", "GHG Protocol"
        ]
        found_skills = [s for s in skill_pool if s.lower() in resume_text.lower()]
        if not found_skills:
            found_skills = ["General Professional Skills"]

        # 4. Domain Specific Keyword Density Analysis (Heuristic Baseline)
        lca_keywords = ['life cycle assessment', 'lca', 'carbon footprint', 'sustainability',
                        'environmental compliance', 'esg', 'emission', 'waste management', 'iso']
        uiux_keywords = ['figma', 'ui/ux', 'wireframe', 'prototyping', 'user research', 'user interface', 'ux design',
                         'mockup', 'usability', 'adobe xd']

        text_lower = resume_text.lower()
        lca_hits = sum(1 for k in lca_keywords if k in text_lower)
        uiux_hits = sum(1 for k in uiux_keywords if k in text_lower)

        lca_score = int(min(98, max(30, 35 + (lca_hits * 10) + int(years * 6))))
        uiux_score = int(min(98, max(30, 35 + (uiux_hits * 8) + int(years * 4))))

        lca_reasoning = f"High domain match: Identified {lca_hits} sustainability/LCA keywords. Tenure: {years} yrs."
        uiux_reasoning = f"Low design alignment ({uiux_hits} design keywords)."

        # 5. Optional Gemini LLM Semantic Enhancement (if API key is present)
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMMI_API_KEY")
        if GEMINI_AVAILABLE and api_key and len(resume_text) > 100:
            try:
                client = genai.Client(api_key=api_key)
                prompt = f"""
                Analyze this candidate resume against two job descriptions and return scores (0-100) and brief reasoning.
                Resume: {resume_text[:2000]}
                JD 1 (LCA Consultant): {jd1_text}
                JD 2 (UI/UX Internship): {jd2_text}
                Format output strictly as:
                LCA_SCORE: [int]
                LCA_REASON: [text]
                UIUX_SCORE: [int]
                UIUX_REASON: [text]
                """
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                res_text = response.text

                lca_match = re.search(r'LCA_SCORE:\s*(\d+)', res_text)
                ui_match = re.search(r'UIUX_SCORE:\s*(\d+)', res_text)
                lca_reas_match = re.search(r'LCA_REASON:\s*(.*?)(?=UIUX_SCORE|$)', res_text, re.DOTALL)
                ui_reas_match = re.search(r'UIUX_REASON:\s*(.*)', res_text, re.DOTALL)

                if lca_match and ui_match:
                    lca_score = int(lca_match.group(1))
                    uiux_score = int(ui_match.group(1))
                    if lca_reas_match:
                        lca_reasoning = "Gemini LLM: " + lca_reas_match.group(1).strip()
                    if ui_reas_match:
                        uiux_reasoning = "Gemini LLM: " + ui_reas_match.group(1).strip()
            except Exception as llm_err:
                pass

        # 6. Smart Role Recommendation Logic
        if lca_score > uiux_score + 10:
            recommended_role = "LCA Consultant Role"
        elif uiux_score > lca_score + 10:
            recommended_role = "UI/UX Design Internship"
        else:
            recommended_role = "LCA Consultant Role" if lca_score >= uiux_score else "UI/UX Design Internship"

        return {
            "candidate_name": candidate_name,
            "email": email,
            "phone": phone,
            "key_skills": found_skills[:6],
            "estimated_years_experience": years,
            "lca_match_score": lca_score,
            "lca_reasoning": lca_reasoning,
            "uiux_match_score": uiux_score,
            "uiux_reasoning": uiux_reasoning,
            "recommended_role": recommended_role,
            "reviewer_status": "Pending",
            "reviewer_notes": ""
        }

    except Exception as e:
        return {
            "candidate_name": "Parsing Error",
            "email": "N/A",
            "phone": "N/A",
            "key_skills": [],
            "estimated_years_experience": 0.0,
            "lca_match_score": 35,
            "lca_reasoning": f"Error: {str(e)}",
            "uiux_match_score": 35,
            "uiux_reasoning": f"Error: {str(e)}",
            "recommended_role": "General / Review Required",
            "reviewer_status": "Pending",
            "reviewer_notes": ""
        }
