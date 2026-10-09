"""Literacy Portal: session-isolated Streamlit assessor workspace."""
import csv
import io
import json
import os
from datetime import date, datetime, timezone
from uuid import uuid4
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Literacy Portal | Assessor", page_icon="📘", layout="wide")
STAGES = {
    "Nursery": ["Sound and action modelling", "Letter recognition", "Oral language and listening", "Story, rhyme and movement"],
    "LKG": ["Vowel sound discrimination", "Two-letter blending", "CVC blending and segmenting", "Decodable sentence practice"],
    "UKG": ["Consonant digraphs", "Vowel digraphs", "Consonant blends", "Reading comprehension and early writing"],
    "Grade 1": ["Word decoding and syllables", "Encoding and dictation", "Sentence fluency", "Comprehension and independent sentences"],
    "Grade 2": ["Multisyllabic word decoding", "Reading fluency", "Comprehension and inference", "Independent composition"],
}
COMMON = ["ELPS lesson design", "Checks for understanding", "Differentiated support", "Evidence and next-step planning"]
RATINGS = {"Not assessed": None, "1 — Needs guided support": 1, "2 — Developing": 2, "3 — Independent": 3, "4 — Can model and coach": 4}

def setting(name, default=""):
    try:
        return st.secrets.get(name, os.environ.get(name, default))
    except FileNotFoundError:
        return os.environ.get(name, default)

def csv_export(rows):
    fields = ["id", "school", "teacher", "stage", "assessment_date", "average", "strengths", "next_steps", "follow_up", "evidence_url", "scores"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        item = dict(row)
        item["scores"] = json.dumps(item.get("scores", {}), ensure_ascii=False)
        for field in fields:
            value = item.get(field)
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                item[field] = "'" + value
        writer.writerow(item)
    return output.getvalue().encode("utf-8-sig")

url, key = setting("SUPABASE_URL"), setting("SUPABASE_PUBLISHABLE_KEY")
demo = str(setting("DEMO_MODE", "true")).lower() == "true"
st.title("📘 Literacy Portal")
st.caption("Assessor workspace · Teacher readiness · Nursery–Grade 2")
if demo:
    st.warning("Demo mode: records exist only in this browser session and disappear when the session ends. Use sample names only.")
    st.session_state.setdefault("demo_records", [])
    user_id, client = "demo", None
else:
    if not url or not key:
        st.error("Add SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY in app Secrets.")
        st.stop()
    # Never cache authenticated clients globally: each browser session owns its client.
    if "client" not in st.session_state:
        st.session_state.client = create_client(url, key)
    client = st.session_state.client
    if not st.session_state.get("signed_in"):
        with st.form("login"):
            st.subheader("Assessor sign in")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign in")
        if submit:
            try:
                result = client.auth.sign_in_with_password({"email": email.strip(), "password": password})
                if result.user and result.session:
                    st.session_state.signed_in = True
                    st.rerun()
                st.error("Sign in was not completed.")
            except Exception:
                st.error("Unable to sign in. Check your credentials and connection.")
        st.stop()
    try:
        user = client.auth.get_user().user
        if not user:
            raise ValueError("Session expired")
        user_id = user.id
        allowed = client.table("literacy_assessors").select("user_id").eq("user_id", user_id).execute().data
        if not allowed:
            st.error("Your account has not been enabled as an assessor. Ask the administrator to add your user ID to literacy_assessors.")
            st.stop()
    except Exception:
        st.error("Cannot verify assessor access. Check your session and database setup.")
        if st.button("Return to sign in"):
            st.session_state.clear()
            st.rerun()
        st.stop()
    st.sidebar.caption(user.email)
    if st.sidebar.button("Sign out"):
        try:
            client.auth.sign_out()
        finally:
            st.session_state.clear()
        st.rerun()

page = st.sidebar.radio("Workspace", ["Overview", "New assessment", "Assessment history", "Literacy progression"])
try:
    if demo:
        records = st.session_state.demo_records
    else:
        records = []
        offset = 0
        while True:
            batch = client.table("literacy_assessments").select("*").eq("assessor_id", user_id).order("created_at", desc=True).order("id").range(offset, offset + 499).execute().data
            records.extend(batch)
            if len(batch) < 500:
                break
            offset += 500
except Exception:
    st.error("Could not load assessments. Run setup.sql and check your connection. No records have been changed.")
    st.stop()

if page == "Overview":
    st.subheader("Teacher growth and student learning, connected")
    a, b, c = st.columns(3)
    a.metric("Assessments", len(records))
    b.metric("Schools", len({r["school"] for r in records}))
    c.metric("Teachers", len({(r["school"], r["teacher"]) for r in records}))
    st.info("Start with New assessment. Record a teacher demonstration, score only the competencies you observed, and agree a practical coaching step.")
    st.caption("Counts refer to your saved assessments. Teacher counts use school + teacher name; they are not a formal roster.")
    st.markdown("**Teacher readiness → Classroom implementation → Student progress**")
    st.write("This version records assessor-led teacher readiness. Student assessments and an incoming teacher-submission queue need a separate roster and submission integration.")
elif page == "New assessment":
    st.subheader("Teacher readiness assessment")
    stage = st.selectbox("Class / stage", list(STAGES))
    st.caption("Working rubric: 1 Needs guided support · 2 Developing · 3 Independent · 4 Can model and coach. Not assessed is excluded from the average.")
    with st.form("assessment_" + stage, clear_on_submit=True):
        left, right = st.columns(2)
        school = left.text_input("School *", max_chars=200)
        teacher = right.text_input("Teacher name *", max_chars=200)
        assessment_date = left.date_input("Assessment date", max_value=date.today())
        follow_up = right.date_input("Follow-up date", value=date.today(), min_value=date.today())
        scores = {}
        for competency in STAGES[stage] + COMMON:
            scores[competency] = RATINGS[st.selectbox(competency, list(RATINGS), key=stage + competency)]
        evidence = st.text_input("Evidence link (optional)", help="Use a permitted HTTPS link. This app does not upload files or grant access to linked evidence.")
        strengths = st.text_area("Observed strengths")
        next_steps = st.text_area("Coaching / next steps *")
        save = st.form_submit_button("Save assessment", type="primary")
    if save:
        measured = [v for v in scores.values() if v is not None]
        from urllib.parse import urlparse
        parsed = urlparse(evidence.strip())
        if not school.strip() or not teacher.strip() or not next_steps.strip() or not measured:
            st.error("Enter school, teacher, next steps and at least one observed score.")
        elif evidence.strip() and (parsed.scheme != "https" or not parsed.netloc):
            st.error("Evidence links must use HTTPS.")
        else:
            row = {"id": str(uuid4()), "assessor_id": user_id, "school": school.strip(), "teacher": teacher.strip(), "stage": stage, "assessment_date": assessment_date.isoformat(), "follow_up": follow_up.isoformat(), "scores": scores, "average": round(sum(measured) / len(measured), 2), "strengths": strengths.strip(), "next_steps": next_steps.strip(), "evidence_url": evidence.strip(), "created_at": datetime.now(timezone.utc).isoformat()}
            try:
                if demo:
                    st.session_state.demo_records.insert(0, row)
                else:
                    saved = client.table("literacy_assessments").insert(row).execute().data
                    if not saved:
                        raise ValueError("No saved record returned")
                st.success("Assessment saved. Open Assessment history to review or export it.")
            except Exception:
                st.error("Save was not confirmed. Check Assessment history before retrying.")
elif page == "Assessment history":
    st.subheader("Your assessment history")
    school_filter = st.selectbox("School", ["All schools"] + sorted({r["school"] for r in records}))
    query = st.text_input("Search teacher").strip().casefold()
    filtered = [r for r in records if (school_filter == "All schools" or r["school"] == school_filter) and query in r["teacher"].casefold()]
    if not filtered:
        st.info("No matching assessments yet.")
    else:
        st.dataframe([{k: r.get(k) for k in ["school", "teacher", "stage", "assessment_date", "average", "follow_up"]} for r in filtered], hide_index=True, width="stretch")
        st.download_button("Download filtered CSV", csv_export(filtered), "literacy_assessments.csv", "text/csv")
        selected = st.selectbox("View assessment", range(len(filtered)), format_func=lambda i: f'{filtered[i]["teacher"]} · {filtered[i]["school"]} · {filtered[i]["assessment_date"]} · {filtered[i]["id"][:8]}')
        row = filtered[selected]
        st.json(row["scores"])
        st.markdown("**Observed strengths**")
        st.text(row["strengths"] or "No strengths recorded")
        st.markdown("**Next steps**")
        st.text(row["next_steps"])
        if row.get("evidence_url"):
            st.link_button("Open evidence", row["evidence_url"])
        st.caption("Assessments are append-only. Record a fresh assessment at follow-up to preserve the original observation.")
else:
    st.subheader("One literacy pathway, five stages")
    st.caption("Editable working progression based on the starter. These are coaching competencies, not a validated standardized assessment.")
    for stage, competencies in STAGES.items():
        with st.expander(stage, expanded=True):
            for competency in competencies:
                st.write("• " + competency)
