import streamlit as st
import pandas as pd
from jinja2 import Template
import smtplib
from email.mime.text import MIMEText

# --- Streamlit UI setup ---
st.set_page_config(page_title="Recruiter Matcher", page_icon="📧", layout="wide")
st.title("📧 Recruiter Email Automator")

# --- Step 1: Upload CSV ---
st.subheader("Step 1: Upload Recruiter CSV")
uploaded_file = st.file_uploader("Upload a CSV with recruiter data", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Loaded {len(df)} recruiters from CSV.")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")
        st.stop()
else:
    st.info("Please upload a CSV file to continue.")
    st.stop()

# --- Step 2: Enter user skills ---
st.subheader("Step 2: Enter your skills")
user_skills = st.text_input("Enter your skills (comma separated)").lower()

if not user_skills:
    st.warning("Please enter at least one skill.")
    st.stop()

user_skills_list = [s.strip() for s in user_skills.split(',')]

# --- Step 3: Match recruiters ---
matched_recruiters = [
    r for _, r in df.iterrows()
    if any(skill in str(r.get('role', '')).lower() or skill in str(r.get('skills', '')).lower()
           for skill in user_skills_list)
]

if not matched_recruiters:
    st.error("❌ No matching recruiters found for your skills.")
    st.stop()

st.success(f"✅ Found {len(matched_recruiters)} matching recruiters!")
matched_df = pd.DataFrame(matched_recruiters)
st.dataframe(matched_df)

# --- Step 4: Email setup ---
st.subheader("Step 3: Email Configuration")
user_email = st.text_input("Enter your Gmail address")
user_password = st.text_input("Enter your Gmail App Password (not your normal password!)", type="password")
sender_name = st.text_input("Enter your name for email signature")

template_text = """
Hi {{ name }},

I came across your profile at {{ company }} regarding the {{ role }} position.
I have experience in {{ skills_list }} and believe my expertise could contribute to your team at {{ company }}.

I am very interested in any current or upcoming opportunities in this role and would love to connect for a quick chat.

Looking forward to your response!

Best regards,
{{ sender_name }}
"""

# --- Step 5: Display email previews and send ---
st.subheader("Step 4: Review and Send Emails")

for i, r in enumerate(matched_recruiters):
    relevant_skills = [s for s in user_skills_list if s in str(r.get('role', '')).lower() or s in str(r.get('skills', '')).lower()]
    skills_str = ", ".join(relevant_skills) if relevant_skills else ", ".join(user_skills_list)

    template = Template(template_text)
    email_body = template.render(
        name=r.get("Full Name", "Recruiter"),
        company=r.get("Company Name", ""),
        role=r.get("role", ""),
        skills_list=skills_str,
        sender_name=sender_name
    )

    with st.expander(f"📧 {r.get('Full Name')} ({r.get('role')}) at {r.get('Company Name')}"):
    edited_email = st.text_area(
        "Edit your email before sending (you can personalize it):",
        value=email_body,
        height=250,
        key=f"email_body_{i}"
    )

    send_email = st.button(f"✉️ Send Email to {r.get('Full Name')}", key=f"send_{i}")

    if send_email:
        if not user_email or not user_password:
            st.error("⚠️ Please provide your Gmail credentials before sending.")
        else:
            try:
                msg = MIMEText(edited_email)  # Use the edited email body here
                msg["Subject"] = f"Job Inquiry - {skills_str.title()}"
                msg["From"] = user_email
                msg["To"] = r.get("email", "")

                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(user_email, user_password)
                    server.send_message(msg)
                st.success(f"✅ Email sent to {r.get('Full Name')}")
            except Exception as e:
                st.error(f"❌ Error sending email: {e}")
