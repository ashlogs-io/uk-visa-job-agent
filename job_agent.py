# ============================================================
# JOB AGENT - Finds UK visa sponsored tech jobs
# ============================================================
# What this script does:
# 1. Searches Adzuna for tech jobs in the UK
# 2. Filters by £41,700 visa salary threshold
# 3. Checks if company is on gov.uk sponsor list
# 4. Uses Claude AI to analyse and score each qualifying job
# ============================================================

import requests
import pandas as pd
import anthropic
from dotenv import load_dotenv
import os

# Load API keys from .env file
load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")       # from developer.adzuna.com
APP_KEY = os.getenv("ADZUNA_APP_KEY")     # from developer.adzuna.com
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY") # from platform.claude.com
SPONSOR_CSV = "sponsor_list.csv"     # filename of gov.uk CSV in same folder
SALARY_THRESHOLD = 41700             # current skilled worker visa threshold
JOB_SEARCH = "cloud engineer"        # what job you are searching for

# MY profie - Claude uses this to score each job
MY_PROFILE = """
BACKGROUND:
- BSc Computer Science, graduated 2024, UK university
- Currently working as Senior Support Worker in care sector
- Did 1 year placement during my degree at Oracle as Site Reliability Engineer Intern
- No commercial tech experience yet
- Age 32, career changer into tech

VISA:
- Currently on Skilled Worker visa
- Needs employer to be a licensed UK visa sponsor
- Needs new Certificate of Sponsorship to switch roles

SKILLS I ACTUALLY HAVE:
- Networking concepts (from degree) - TCP/IP, DNS, subnets
- Basic programming logic (from degree)
- Confident with computers and troubleshooting
- Strong communication and people skills from support work

CURRENTLY STUDYING:
- AWS Solution Architect Associate (in progress)
- Microsoft AZ-900 Azure Fundamentals (in progress)
- Practicing on AWS and Azure free tier

LOCATION:
- Based in Preston but open to relocating for the right role
- Prefer remote or anywhere in the UK

TARGET ROLES (in order of preference):
- Junior Cloud Engineer / Azure/ AWS Associate
- IT Support Analyst
- Junior Systems Administrator
- Graduate IT roles
- AWS/Azure Administrator, 
- Junior SRE, 
- DevOps

WHAT I CANNOT DO:
- Roles requiring Security Clearance (SC/DV) - difficult on visa
- Roles below £41,700 - does not meet visa threshold
- Roles at companies not on the gov.uk sponsor register
"""

# ============================================================
# STEP 1 - Load the gov.uk sponsor list
# ============================================================

print("Loading sponsor list...")
sponsor_df = pd.read_csv(SPONSOR_CSV, encoding="latin-1")

# Strip any hidden spaces from company names in the list
sponsor_df["Organisation Name"] = sponsor_df["Organisation Name"].str.strip()

print(f"Loaded {len(sponsor_df)} licensed sponsors\n")

# ============================================================
# STEP 2 - Define a function to check if a company sponsors visas
# ============================================================

# These are words that appear in company names but are not
# part of the core name - removing them helps matching
NOISE_WORDS = [
    " limited", " ltd", " ltd.", " plc", " plc.",
    " (uk)", " uk", " inc", " llc", " group",
    " services", " solutions", " technologies",
    " technology", " consulting", " international"
]

def clean_name(name):
    # Lowercase and strip spaces
    cleaned = name.lower().strip()
    # Remove noise words
    for word in NOISE_WORDS:
        cleaned = cleaned.replace(word, "")
    # Remove brackets and extra spaces
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()

def is_visa_sponsor(company_name):
    # Clean the company name from Adzuna
    cleaned_search = clean_name(company_name)

    # Search the sponsor list for a match
    matches = sponsor_df[
        sponsor_df["Organisation Name"].str.lower().str.contains(
            cleaned_search,
            na=False
        )
    ]

    return len(matches) > 0

# ============================================================
# STEP 3 - Claude AI analysis function
# ============================================================

# Connect to Claude
claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

def analyse_job_with_ai(title, company, location, salary, description):

    print(f" Asking Claude to analyse this role...")

    # This is the message we sent to Claude
    message = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system="""You are a UK tech career adviros helping an international candidate find visa sponsored jobs. 
        Be concise and practical. 
        Always respond in this exact format:

        SCORE: [number from 1-10]
        VERDICT: [one sentence - is this worth applying for?]
        GOOD POINTS: [2-3 bullet points of why this suits the candidate]
        WATCH OUT: [1-2 things to be aware of]
        """,
        messages=[
            {
                "role": "user",
                "content": f"""
                Analyse this job for my profile:

                MY PROFILE:
                {MY_PROFILE}

                JOB DETAILS:
                Title: {title}
                Company: {company}
                Location: {location}
                Salary: {salary}
                Description: {description[:1000]}

                How good a match is this for me?
                """
            }
        ]
    )

    return message.content[0].text

# ============================================================
# STEP 4 - Search Adzuna for jobs
# ============================================================

print(f"Searching for: {JOB_SEARCH}")
print(f"Salary threshold: £{SALARY_THRESHOLD:,}\n")

url = "https://api.adzuna.com/v1/api/jobs/gb/search/1"

params = {
    "app_id": APP_ID,
    "app_key": APP_KEY,
    "what": JOB_SEARCH,
    "where": "UK",
    "results_per_page": 10
}

response = requests.get(url, params=params)
data = response.json()

print(f"Adzuna found {data['count']} total jobs")
print(f"Checking first 10...\n")
print("-" * 50)

# ============================================================
# STEP 5 - Filter jobs by salary and sponsorship
# ============================================================

qualifying_jobs = []

for job in data["results"]:

    title = job["title"]
    company = job["company"]["display_name"]
    location = job["location"]["display_name"]
    link = job["redirect_url"]
    description = job.get("description", "No description available")
    salary_min = job.get("salary_min", None)
    salary_max = job.get("salary_max", None)

    # Check 1 - Salary threshold
    if salary_min is not None and salary_min < SALARY_THRESHOLD:
        print(f"X SALARY TOO LOW  | {title} at {company} | £{int(salary_min):,}")
        continue

    # Check 2 - Visa sponsorship
    if not is_visa_sponsor(company):
        print(f"X NOT ON SPONSOR LIST | {title} at {company}")
        continue

    # Passed both checks
    if salary_min is None:
        salary_display = "Salary not listed"
    else:
        salary_display = f"£{int(salary_min):,} - £{int(salary_max):,}"

    print(f"\n✓ PASSED FILTERS | {title} at {company} | {salary_display}")

    # Check 3 - Ask Claude to analyse this job
    ai_analysis = analyse_job_with_ai(
        title,
        company,
        location,
        salary_display,
        description
    )

    qualifying_jobs.append({
        "title": title,
        "company": company,
        "location": location,
        "salary": salary_display,
        "link": link,
        "ai_analysis": ai_analysis
    })

    print(f"\n✓ GOOD MATCH | {title} at {company} | {salary_display}")

# ============================================================
# STEP 6 - Print the final results
# ============================================================

print("\n")
print("-" * 50)
print(f"RESULTS: {len(qualifying_jobs)} jobs passed all checks:\n")
print("=" * 50)

for i, job in enumerate(qualifying_jobs, 1):
    print(f"Job {i}:")
    print(f"  Title:    {job['title']}")
    print(f"  Company:  {job['company']}")
    print(f"  Location: {job['location']}")
    print(f"  Salary:   {job['salary']}")
    print(f"  Link:     {job['link']}")
    print(f"\n AI Anlysis:")
    print(job['ai_analysis'])
    print("-" * 50)