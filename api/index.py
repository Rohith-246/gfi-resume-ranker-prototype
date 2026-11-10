from flask import Flask, render_template, request
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.parser import extract_text_from_pdf
from utils.matcher import evaluate_resume

app = Flask(__name__, template_folder="../templates", static_folder="../static")

SAMPLE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/resumes'))

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    bulk_results = None
    error = None
    
    sample_files = []
    if os.path.exists(SAMPLE_DIR):
        sample_files = sorted([f for f in os.listdir(SAMPLE_DIR) if f.lower().endswith(('.pdf', '.docx'))])

    if request.method == "POST":
        action = request.form.get("action")
        
        try:
            jd1 = "LifeCycle Assessment (LCA) Consultant role: 4-6 years experience."
            jd2 = "UI/UX Design Internship: User research, wireframing, Figma."

            if action == "bulk_evaluate":
                bulk_results = []
                target_files = sample_files[:10]  # Top 10 fast preview
                for file in target_files:
                    file_path = os.path.join(SAMPLE_DIR, file)
                    text = extract_text_from_pdf(file_path)
                    res = evaluate_resume(text, jd1, jd2)
                    res["filename"] = file
                    bulk_results.append(res)
                bulk_results = sorted(bulk_results, key=lambda x: x['lca_match_score'], reverse=True)
            
            else:
                selected_sample = request.form.get("sample_resume")
                uploaded_file = request.files.get("resume")
                
                if selected_sample and selected_sample != "":
                    file_path = os.path.join(SAMPLE_DIR, selected_sample)
                    text = extract_text_from_pdf(file_path)
                    filename = selected_sample
                elif uploaded_file and uploaded_file.filename != '':
                    text = extract_text_from_pdf(uploaded_file)
                    filename = uploaded_file.filename
                else:
                    raise ValueError("Please select a pre-loaded resume or upload a file.")

                result = evaluate_resume(text, jd1, jd2)
                result["filename"] = filename
                
        except Exception as e:
            error = f"Error processing evaluation: {str(e)}"
            
    return render_template("index.html", result=result, bulk_results=bulk_results, error=error, sample_files=sample_files)

if __name__ == "__main__":
    app.run(debug=True)
