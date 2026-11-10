import streamlit as st
import pandas as pd
import os
from glob import glob
from utils.parser import extract_text_from_pdf
from utils.matcher import evaluate_resume
from utils.reporter import generate_executive_report

try:
    import boto3

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

st.set_page_config(
    page_title="Growth For Impact | Enterprise AI Screening",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱 Growth For Impact (GFI) — Enterprise Candidate Screening & Executive RAG Engine")
st.markdown(
    "Powered by Hybrid Gemini LLM / TF-IDF Semantic Scoring, AWS S3 Cloud Storage, Executive PDF Reporting, and Interactive Reviewer Workflows.")

st.markdown("---")

st.subheader("📋 Target Job Descriptions & Official GFI Openings")
col_jd1, col_jd2 = st.columns(2)

with col_jd1:
    st.markdown("### 🎯 LCA Consultant Role")
    st.markdown("**Location:** Chennai based / Relocate")
    st.markdown(
        "**Core Focus:** Life Cycle Assessment (LCA) methodologies, carbon footprint modeling, sustainability reporting, and environmental impact analysis.")
    st.markdown("[🔗 Official GFI LCA Application Form](https://tally.so/r/9q5plp)")
    default_jd1 = "LifeCycle Assessment (LCA) Consultant role (Chennai based/relocate): 4-6 years experience. Requires deep sustainability analysis, carbon footprint modeling, LCA methodologies, environmental impact assessment, and technical reporting."

with col_jd2:
    st.markdown("### 🎨 UI/UX Design Internship")
    st.markdown("**Location:** Remote / Hybrid")
    st.markdown(
        "**Core Focus:** User research, wireframing, high-fidelity prototyping, Figma proficiency, user testing, interaction design, and product portfolio evaluation.")
    st.markdown("[🔗 Official GFI UI/UX Internship Form](https://tally.so/r/0QovpQ)")
    default_jd2 = "UI/UX Design Internship role: Focus on user research, wireframing, prototyping, Figma proficiency, user testing, interaction design, and portfolio demonstrating intuitive digital products."

with st.expander("⚙️ Advanced: Configure Rubric Weights & Criteria Prompts"):
    col_w1, col_w2, col_w3, col_w4 = st.columns(4)
    with col_w1:
        w_skills = st.slider("Skills Weight", 0.0, 1.0, 0.4)
    with col_w2:
        w_exp = st.slider("Experience Weight", 0.0, 1.0, 0.3)
    with col_w3:
        w_domain = st.slider("Domain Fit", 0.0, 1.0, 0.2)
    with col_w4:
        w_action = st.slider("Action Verbs", 0.0, 1.0, 0.1)

    jd1_input = st.text_area("Edit LCA Criteria", default_jd1, height=80)
    jd2_input = st.text_area("Edit UI/UX Criteria", default_jd2, height=80)

if 'jd1_input' not in locals():
    jd1_input = default_jd1
    jd2_input = default_jd2
    w_skills, w_exp, w_domain, w_action = 0.4, 0.3, 0.2, 0.1

st.markdown("---")
st.header("📂 Resume Pile Processing & Ingestion (Local or AWS S3 Cloud)")

source_mode = st.radio("Select Resume Source:", ["Local Project Folder", "AWS S3 Cloud Bucket", "Manual File Upload"])
all_files_to_process = []

if source_mode == "Local Project Folder":
    load_local_data = st.checkbox("Auto-load resumes from local project folder (`data/resumes/` or workspace)",
                                  value=True)
    if load_local_data:
        local_doc_paths = glob("**/anonymized_*.docx", recursive=True) + glob("**/data/resumes/*.docx",
                                                                              recursive=True) + glob("*.docx") + glob(
            "data/resumes/*.docx")
        local_doc_paths = list(set(local_doc_paths))
        if local_doc_paths:
            st.success(f"📁 Successfully detected {len(local_doc_paths)} candidate document(s).")
            for p in local_doc_paths:
                all_files_to_process.append(("local", p))
        else:
            st.info("ℹ️ Local resume folder is empty.")

elif source_mode == "AWS S3 Cloud Bucket":
    st.markdown("#### ☁️ AWS S3 Cloud Bucket (Auto-Linked)")
    s3_bucket = st.text_input("Linked S3 Bucket Name",
                              value="gfi-candidate-resumes-rohith-289705191824-ap-southeast-2-an")
    s3_region = st.text_input("AWS Region", value="ap-southeast-2")

    if st.button("📥 Pull Resumes from Linked AWS S3 Bucket"):
        if not BOTO3_AVAILABLE:
            st.error("❌ `boto3` library is not installed. Please run `pip install boto3`.")
        elif not s3_bucket:
            st.error("❌ Please configure your S3 Bucket Name.")
        else:
            try:
                s3 = boto3.client('s3', region_name=s3_region)
                temp_dir = "data/resumes_s3"
                os.makedirs(temp_dir, exist_ok=True)

                response = s3.list_objects_v2(Bucket=s3_bucket)
                if "Contents" in response:
                    downloaded_count = 0
                    for obj in response["Contents"]:
                        key = obj["Key"]
                        if key.endswith(('.pdf', '.docx')):
                            local_path = os.path.join(temp_dir, os.path.basename(key))
                            s3.download_file(s3_bucket, key, local_path)
                            all_files_to_process.append(("local", local_path))
                            downloaded_count += 1
                    st.success(f"✅ Successfully synced {downloaded_count} resume(s) from S3 bucket `{s3_bucket}`!")
                else:
                    st.warning(
                        "⚠️ S3 bucket is empty. (You can also use Local Project Folder since resumes are in your workspace).")
            except Exception as e:
                st.error(f"❌ S3 Connection Error: {str(e)}")

elif source_mode == "Manual File Upload":
    uploaded_files = st.file_uploader("Upload candidate resumes", type=["pdf", "docx"], accept_multiple_files=True)
    if uploaded_files:
        for f in uploaded_files:
            all_files_to_process.append(("uploaded", f))

if all_files_to_process:
    if st.button("🚀 Run Hybrid AI Vector Extraction & Multi-Role Ranking", type="primary"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_files = len(all_files_to_process)
        for i, (source_type, file_ref) in enumerate(all_files_to_process):
            filename = os.path.basename(file_ref) if source_type == "local" else file_ref.name

            status_text.text(f"Processing candidate ({i + 1}/{total_files}): {filename}...")
            text = extract_text_from_pdf(file_ref)

            if "Error" in text or not text.strip():
                results.append({
                    "filename": filename,
                    "candidate_name": "Unreadable Document",
                    "email": "N/A",
                    "phone": "N/A",
                    "key_skills": [],
                    "estimated_years_experience": 0.0,
                    "lca_match_score": 0,
                    "lca_reasoning": "Extraction Error",
                    "uiux_match_score": 0,
                    "uiux_reasoning": "Extraction Error",
                    "recommended_role": "Uncertain",
                    "reviewer_status": "Pending",
                    "reviewer_notes": ""
                })
            else:
                evaluation = evaluate_resume(text, jd1_input, jd2_input, weights=(w_skills, w_exp, w_domain, w_action))
                evaluation["filename"] = filename
                results.append(evaluation)

            progress_bar.progress((i + 1) / total_files)

        status_text.text("✅ All candidates successfully analyzed and ranked!")
        df = pd.DataFrame(results)
        st.session_state['df_results'] = df

if 'df_results' in st.session_state:
    df = st.session_state['df_results']
    st.markdown("---")

    st.header("📊 Executive Analytics & PDF Report Export")
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Total Scanned", len(df))
    with col_stat2:
        st.metric("LCA Recommended", len(df[df['recommended_role'] == 'LCA Consultant Role']))
    with col_stat3:
        st.metric("UI/UX Recommended", len(df[df['recommended_role'] == 'UI/UX Design Internship']))
    with col_stat4:
        avg_score = int(df[['lca_match_score', 'uiux_match_score']].max(axis=1).mean())
        st.metric("Avg Match Parity", f"{avg_score}%")

    if st.button("📄 Generate Executive PDF Summary Report"):
        report_path = generate_executive_report(df)
        with open(report_path, "rb") as pdf_file:
            st.download_button(
                label="📥 Download Executive PDF Report",
                data=pdf_file,
                file_name="gfi_executive_screening_report.pdf",
                mime="application/pdf"
            )
        st.success("✅ Executive PDF Report generated successfully!")

    st.markdown("---")
    st.header("🔍 Natural Language RAG Candidate Search")
    search_query = st.text_input(
        "Search candidate pool by skill, keyword, or role (e.g., 'Python', 'Figma', 'Carbon'):")

    display_df = df
    if search_query:
        query_lower = search_query.lower()
        display_df = df[df.apply(lambda row: query_lower in str(row['key_skills']).lower() or
                                             query_lower in str(row['candidate_name']).lower() or
                                             query_lower in str(row['lca_reasoning']).lower() or
                                             query_lower in str(row['uiux_reasoning']).lower(), axis=1)]
        st.info(f"Found {len(display_df)} candidate(s) matching '{search_query}'")

    st.markdown("---")
    st.header("📋 Human Reviewer Dashboard & Interview Dispatcher")

    tab1, tab2, tab3 = st.tabs(
        ["🎯 LCA Consultant Rankings", "🎨 UI/UX Internship Rankings", "📋 Complete Data Matrix & Actions"])

    with tab1:
        st.subheader("Top Ranked Candidates for LCA Consultant Role")
        lca_ranked = display_df.sort_values(by="lca_match_score", ascending=False)
        for idx, row in lca_ranked.iterrows():
            with st.expander(
                    f"Rank {idx + 1}: {row.get('candidate_name')} ({row.get('filename')}) — LCA Score: {row.get('lca_match_score')}/100"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Recommended Role Fit:** {row.get('recommended_role')}")
                    st.markdown(f"**Estimated Experience:** {row.get('estimated_years_experience')} years")
                    st.markdown(f"**Email:** {row.get('email')} | **Phone:** {row.get('phone')}")
                    st.markdown(f"**Key Skills:** {', '.join(row.get('key_skills', []))}")
                    st.markdown(f"**Review Status:** {row.get('reviewer_status')}")
                with c2:
                    st.markdown(f"**Evidence & Reasoning:** {row.get('lca_reasoning')}")
                    mail_subject = "Interview Invitation: Growth For Impact - LCA Consultant Role"
                    mail_body = f"Hi {row.get('candidate_name')},\n\nWe reviewed your resume for the LCA Consultant position at Growth For Impact and would love to schedule an interview.\n\nBest regards,\nGFI Hiring Team"
                    st.markdown(
                        f"[✉️ Send Interview Invitation Email](mailto:{row.get('email')}?subject={mail_subject}&body={mail_body})")

    with tab2:
        st.subheader("Top Ranked Candidates for UI/UX Design Internship")
        uiux_ranked = display_df.sort_values(by="uiux_match_score", ascending=False)
        for idx, row in uiux_ranked.iterrows():
            with st.expander(
                    f"Rank {idx + 1}: {row.get('candidate_name')} ({row.get('filename')}) — UI/UX Score: {row.get('uiux_match_score')}/100"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Recommended Role Fit:** {row.get('recommended_role')}")
                    st.markdown(f"**Estimated Experience:** {row.get('estimated_years_experience')} years")
                    st.markdown(f"**Email:** {row.get('email')} | **Phone:** {row.get('phone')}")
                    st.markdown(f"**Key Skills:** {', '.join(row.get('key_skills', []))}")
                    st.markdown(f"**Review Status:** {row.get('reviewer_status')}")
                with c2:
                    st.markdown(f"**Evidence & Reasoning:** {row.get('uiux_reasoning')}")
                    mail_subject = "Interview Invitation: Growth For Impact - UI/UX Internship"
                    mail_body = f"Hi {row.get('candidate_name')},\n\nWe reviewed your resume for the UI/UX Design Internship at Growth For Impact and would love to schedule an interview.\n\nBest regards,\nGFI Hiring Team"
                    st.markdown(
                        f"[✉️ Send Interview Invitation Email](mailto:{row.get('email')}?subject={mail_subject}&body={mail_body})")

    with tab3:
        st.subheader("Interactive Reviewer Matrix & Status Management")
        edited_df = st.data_editor(display_df, num_rows="dynamic")

        csv_data = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Updated Screening Matrix with Reviewer Notes",
            data=csv_data,
            file_name="gfi_resume_screening_reviewed.csv",
            mime="text/csv",
        )
