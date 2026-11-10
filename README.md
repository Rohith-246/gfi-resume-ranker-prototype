# 🌱 Growth For Impact (GFI) — AI Resume Screening & Multi-Role Ranking Engine

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-TF--IDF-orange.svg)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blueviolet.svg)](https://docker.com/)

An enterprise-grade, multi-role candidate screening prototype built for **Growth For Impact (GFI)**. This system automates the ingestion, semantic matching, evaluation, and executive reporting for candidate resume piles across distinct roles: **LCA Consultant** and **UI/UX Design Internship**.

---

## 🚀 Key Features

1. **Robust Multi-Format Ingestion:** Deep paragraph and table extraction for `.docx` and `.pdf` resume piles.
2. **TF-IDF Semantic Vector Similarity:** Evaluates candidate competency against job descriptions using cosine similarity rather than rigid keyword counting.
3. **Precision Date-Range Experience Parser:** Automatically calculates true professional tenure from work history intervals.
4. **Configurable Rubric Weighting:** Dynamic sidebar sliders for HR reviewers to tune skill vs. experience weights.
5. **Natural Language RAG Search:** Instantly query the candidate pool using keywords or skills.
6. **Executive PDF Report Generator:** Instantly compile top-ranked candidates into a polished PDF report.
7. **Interactive HR Reviewer Workflow:** Assign status tags (*Pending*, *Shortlisted*, *Interviewed*, *Rejected*) and notes, exportable to CSV.

---

## 🛠️ Project Structure
```text
gfi-resume-ranker-prototype/
├── app.py                   # Main Streamlit dashboard interface
├── requirements.txt         # Project dependencies
├── Dockerfile               # Containerization configuration
├── utils/
│   ├── parser.py            # Robust PDF & Word document parser
│   ├── matcher.py           # TF-IDF vector similarity & scoring engine
│   └── reporter.py          # Executive PDF report generator
└── data/
    └── resumes/             # Candidate resume files (.docx / .pdf)
