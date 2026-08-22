from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Job Search Copilot",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Job Search Copilot")
st.caption("Excel stores the pipeline. This app tells me what needs attention.")

with st.expander("How it works"):
    st.markdown("""
1. I track applications, contacts and next actions in Excel.
2. The app reads the pipeline and identifies what needs attention today.
3. It classifies each action as an application, follow-up, networking task or interview preparation.
4. It builds a context-specific prompt that I can use with Claude to decide or draft the next step.

I built it because my spreadsheet was good at storing information, but not at telling me what to do next.
""")

# --------------------------------------------------
# LOAD EXCEL
# --------------------------------------------------

default_paths = [
    Path("Luca_Job_Search_Tracker.xlsx"),
    Path("../Luca_Job_Search_Tracker.xlsx"),
]

local_file = next((p for p in default_paths if p.exists()), None)

with st.sidebar:
    st.header("Tracker")
    uploaded = st.file_uploader(
        "Or upload your tracker",
        type=["xlsx"]
    )

if uploaded is not None:
    source = uploaded
    source_name = uploaded.name
elif local_file:
    source = local_file
    source_name = str(local_file)
else:
    st.error(
        "I can't find Luca_Job_Search_Tracker.xlsx. "
        "Put it in your Downloads folder or upload it from the sidebar."
    )
    st.stop()

try:
    df = pd.read_excel(source, sheet_name="Applications")
except Exception as e:
    st.error(f"Could not read the Excel tracker: {e}")
    st.stop()

# Remove empty template rows
df = df[df["Company"].notna()].copy()
df = df[df["Company"].astype(str).str.strip() != ""]

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

date_columns = [
    "Applied Date",
    "Last Contact",
    "Next Action Date",
]

for col in date_columns:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

def clean(value):
    if pd.isna(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return str(value)

def days_since(value):
    if pd.isna(value):
        return None
    return (date.today() - value.date()).days

def determine_action(row):
    status = clean(row.get("Status")).lower()
    priority = clean(row.get("Priority")).upper()

    if status in ["rejected", "offer", "withdrawn", "closed"]:
        return None

    next_date = row.get("Next Action Date")
    next_action = clean(row.get("Next Action"))

    # Explicit action set in Excel
    if pd.notna(next_date) and next_date.date() <= date.today():
        days_overdue = (date.today() - next_date.date()).days

        return {
            "action": next_action or "Review application",
            "urgency": 5 if days_overdue > 2 else 4,
            "reason": (
                f"{days_overdue} days overdue"
                if days_overdue > 0
                else "Due today"
            ),
        }

    last_contact = row.get("Last Contact")
    applied_date = row.get("Applied Date")

    # Interview follow-up
    if "interview" in status and pd.notna(last_contact):
        days = days_since(last_contact)
        if days is not None and days >= 3:
            return {
                "action": "Follow up after interview",
                "urgency": 5,
                "reason": f"{days} days since last contact",
            }

    # Normal recruiter/application follow-up
    anchor = last_contact if pd.notna(last_contact) else applied_date

    if (
        status in ["applied", "contacted", "application sent"]
        and pd.notna(anchor)
    ):
        days = days_since(anchor)

        if days >= 10:
            urgency = 5
        elif days >= 7:
            urgency = 4
        elif days >= 5:
            urgency = 3
        else:
            urgency = 0

        if urgency:
            return {
                "action": "Follow up",
                "urgency": urgency,
                "reason": f"{days} days since last interaction",
            }

    return None

def priority_score(value):
    value = clean(value).upper()

    if value.startswith("A"):
        return 3
    if value.startswith("B"):
        return 2
    if value.startswith("C"):
        return 1
    return 0

def build_prompt(row, action):
    action_text = clean(action["action"])
    action_lower = action_text.lower()

    if "interview" in action_lower:
        mode = """
This is INTERVIEW PREPARATION.
Do not draft a message unless clearly necessary.
Give me:
1. the 3 most important things to research,
2. the 5 questions I should prepare for,
3. the 3 strongest points from my background to emphasize,
4. one concrete preparation task to do now.
Keep it concise and practical.
"""

    elif any(word in action_lower for word in ["network", "linkedin", "reach out", "contact"]):
        mode = """
This is a NETWORKING action.
Draft a short, natural outreach message.
It should feel personal rather than transactional.
Use prior relationships or context from the notes.
Do not directly ask for a referral unless the context clearly supports it.
Keep the message under 120 words.
"""

    elif "follow" in action_lower or "wait" in action_lower:
        mode = """
This is a FOLLOW-UP action.
Decide first whether a follow-up is appropriate based on the dates and context.
If yes, draft a short natural follow-up message in English.
Use previous interactions from the notes.
Do not sound desperate, generic or overly formal.
Keep it under 120 words.
If it is too early, tell me when I should follow up instead.
"""

    elif any(word in action_lower for word in ["apply", "application", "cover letter", "demo", "cv"]):
        mode = """
This is an APPLICATION action.
Do not draft a recruiter message.
Tell me exactly what I should complete before submitting the application.
Use the notes and next action to create a short actionable checklist.
Prioritise anything that could materially improve the application.
If the application requires a demo, portfolio item, cover letter or tailored CV, address those specifically.
"""

    else:
        mode = """
This is a GENERAL JOB-SEARCH action.
Tell me the most useful next step to take now.
Be concise and practical.
"""

    return f"""You are my personal job-search copilot.

Next action:
{action_text}

Company: {clean(row.get("Company"))}
Role: {clean(row.get("Role"))}
Location: {clean(row.get("Location"))}
Priority: {clean(row.get("Priority"))}
Status: {clean(row.get("Status"))}
Applied date: {clean(row.get("Applied Date"))}
Contact name: {clean(row.get("Contact Name"))}
Contact channel: {clean(row.get("Channel"))}
Last contact: {clean(row.get("Last Contact"))}
Notes: {clean(row.get("Notes"))}

{mode}

Do not invent information.
Do not exaggerate my experience.
Return only the useful output."""


# --------------------------------------------------
# CREATE ACTION QUEUE
# --------------------------------------------------

actions = []

for idx, row in df.iterrows():
    action = determine_action(row)

    if action:
        actions.append({
            "index": idx,
            "urgency": action["urgency"],
            "priority_score": priority_score(row.get("Priority")),
            "action": action,
        })

actions.sort(
    key=lambda x: (x["urgency"], x["priority_score"]),
    reverse=True
)

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

closed_statuses = ["rejected", "withdrawn", "closed"]

active = df[
    ~df["Status"]
    .fillna("")
    .astype(str)
    .str.lower()
    .isin(closed_statuses)
]

interviews = df[
    df["Status"]
    .fillna("")
    .astype(str)
    .str.lower()
    .str.contains("interview")
]

high_priority = df[
    df["Priority"]
    .fillna("")
    .astype(str)
    .str.upper()
    .str.startswith("A")
]

c1, c2, c3, c4 = st.columns(4)

c1.metric("Active applications", len(active))
c2.metric("Actions due", len(actions))
c3.metric("High priority", len(high_priority))
c4.metric("Interviews", len(interviews))

st.caption(f"Reading: {source_name}")

# --------------------------------------------------
# TODAY QUEUE
# --------------------------------------------------

st.subheader("🔥 Today")

if not actions:
    st.success("Nothing needs attention right now.")
else:
    for item in actions:
        row = df.loc[item["index"]]
        action = item["action"]

        company = clean(row.get("Company"))
        role = clean(row.get("Role"))
        priority = clean(row.get("Priority"))

        title = (
            f"{company} — {role} | "
            f"{action['action']} | Priority {priority}"
        )

        with st.expander(title):

            st.write(f"**Why:** {action['reason']}")

            contact = clean(row.get("Contact Name"))
            if contact:
                st.write(f"**Contact:** {contact}")

            notes = clean(row.get("Notes"))
            if notes:
                st.write(f"**Context:** {notes}")

            prompt = build_prompt(row, action)

            st.markdown("**Prompt for Claude**")
            st.text_area(
                "Copy this into Claude Free:",
                prompt,
                height=330,
                key=f"prompt_{item['index']}"
            )

# --------------------------------------------------
# FULL PIPELINE
# --------------------------------------------------

st.subheader("📋 Full pipeline")

display_columns = [
    "Company",
    "Role",
    "Location",
    "Priority",
    "Status",
    "Applied Date",
    "Contact Name",
    "Last Contact",
    "Next Action Date",
    "Next Action",
]

existing = [c for c in display_columns if c in df.columns]

display_df = df[existing].copy()

for col in ["Applied Date", "Last Contact", "Next Action Date"]:
    if col in display_df.columns:
        display_df[col] = display_df[col].apply(
            lambda x: x.strftime("%Y-%m-%d")
            if pd.notna(x) and hasattr(x, "strftime")
            else ""
        )

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
)

st.info(
    "Excel is the source of truth. "
    "Update the tracker in Excel, save it, then refresh this page."
)
