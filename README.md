# Job Search Copilot

A small tool I built to help manage my own job search.

I was already tracking applications in Excel, but after a few days I realised the spreadsheet was good at storing information and not very good at answering a more useful question:

**What should I actually do today?**

So I built a small layer on top of it.

## What it does

The Excel file stays the source of truth for applications, contacts and dates.

The app reads that pipeline and:

* shows the applications that need attention
* identifies overdue or scheduled actions
* prioritises them based on timing and application priority
* distinguishes between applications, follow-ups, networking and interview preparation
* builds a context-specific prompt that I can use with Claude for the next step

For example, a follow-up produces a prompt for a short recruiter message, while an application task produces a checklist of what still needs to be completed.

## Why I built it this way

My first version tried to replace the spreadsheet entirely.

After using it, I realised that made little sense. Excel was already better at editing and storing the data.

The useful part was everything that happened **after** the data was stored: deciding what needed attention and preparing the next action.

So I kept Excel as the simple database and turned the app into a lightweight job-search copilot instead.

## How I use it

My tracker contains information such as:

* company and role
* location
* application priority
* current status
* application date
* contact person
* last interaction
* next action and deadline
* notes and previous context

I update the spreadsheet as I apply and speak with people.

When I open the app, it turns that information into a daily action queue.

## Built with

* Python
* Streamlit
* Pandas
* OpenPyXL
* Claude for AI-assisted next steps

I also used AI extensively while building and iterating on the project itself. The goal was not to write every line manually, but to see how quickly I could go from a real annoyance to something I could actually use.

## Running it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app expects an Excel workbook with a sheet called `Applications`.

My actual job-search tracker is intentionally not included in the repository because it contains personal information and recruiter contacts.

## What I would improve next

If I keep using it, the next things I would probably add are:

* automatically importing basic information from a job posting
* a better way to track multiple contacts at the same company
* weekly statistics on applications and interview conversion
* optional direct LLM integration instead of manually copying the generated prompt
* reminders for actions that become overdue

This is deliberately a small project. I built it because I had the problem myself, and I wanted something useful quickly rather than a much bigger system I would never actually use.
