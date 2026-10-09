# Literacy Portal — Streamlit Assessor

Python conversion of the supplied Next.js starter. Includes assessor sign-in, overview, teacher-readiness rubric for Nursery–Grade 2, evidence links, coaching notes, follow-up dates, saved history, and filtered CSV export.

## Deploy to Streamlit Community Cloud

1. Extract this ZIP. Upload the CONTENTS of streamlit-assessor to a new GitHub repository, or a separate folder/branch in Vision. Keep app.py and requirements.txt together. Include .streamlit/config.toml.
2. Open https://share.streamlit.io and choose Create app. Select your GitHub repository and branch, then set the main file path to app.py (or your-folder/app.py if nested).
3. In Advanced settings select Python 3.11. Paste secrets.example.toml into Secrets. Leave DEMO_MODE = "true" for the initial smoke test.
4. Deploy. In New assessment create a sample assessment, then check Assessment history and download the CSV.
5. To enable persistent real records, run setup.sql once in your Supabase SQL Editor. It creates literacy_assessors and literacy_assessments. Do not rerun it after creation; it intentionally fails if those tables already exist.
6. Create an email/password user in Supabase Authentication. Copy that user's UUID and run the commented insert at the bottom of setup.sql, replacing ACTUAL-AUTH-USER-UUID.
7. In Streamlit Secrets set DEMO_MODE = "false", your project's SUPABASE_URL, and SUPABASE_PUBLISHABLE_KEY. Save, restart and sign in. Use a publishable key (or legacy anon key), never a service-role key.
8. Verify: save and reload an assessment; sign out; check that another authorized assessor cannot see your records and an unapproved account cannot assess. Database RLS enforces per-assessor ownership.

## Run locally

Use Python 3.11:

    python -m pip install -r requirements.txt
    python -m streamlit run app.py

Default mode is a session-only demo. For real persistence copy secrets.example.toml to .streamlit/secrets.toml and configure as above. Never commit secrets.toml.

## Scope and data

The original archive was a login/dashboard shell, so there is no teacher submission database to migrate. This version adds assessor-entered teacher-readiness records. It does not connect teacher_records, classroom_observations, a school roster, student assessments, or an incoming submission queue. Each approved assessor sees only their own assessments; school leader and shared school access need membership policies in a future extension.

The rubric is an editable working rubric rather than a validated assessment. Unobserved competencies are excluded from the mean. Records are append-only for observation history. Evidence is an external HTTPS link; access must already be granted by the evidence owner. Demo data disappears when the browser session ends. Real records remain in Supabase across Streamlit restarts.

## Validation

See VALIDATION.md for checks run during preparation. No live hosting account or production database is configured in this package. The ZIP is deployment-ready source, not a published Streamlit URL.
