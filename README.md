# Job Follow-up Agent

A small personal AI tool I built to make my own job search less chaotic.

It keeps applications in one place, calculates which ones are due for a follow-up, and can use Claude to draft a short follow-up based on the company, role, status and my notes.

## Why I built it

When I started applying seriously after finishing university, I noticed that the annoying part was not finding jobs — it was remembering who I had contacted, when I should follow up, and what context mattered for each conversation.

I wanted something simple enough that I would actually use it, so I built this instead of using a large CRM.

## What it does

- Imports a CSV of applications
- Keeps the tracker editable in the browser
- Scores follow-up urgency using simple, transparent rules
- Creates a follow-up queue
- Uses Claude to draft a concise message using the context I saved
- Exports the updated tracker back to CSV

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"
streamlit run app.py
```

The tracker still works without an API key; only AI message drafting is disabled.

## Input format

See `sample_applications.csv`.

## What I would add next

- Gmail/LinkedIn reminders
- Automatic extraction of company and role information from a job URL
- A weekly summary of applications that need attention
- Better prioritisation based on role quality and relationship strength
