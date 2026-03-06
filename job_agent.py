# ============================================================
# JOB AGENT - Finds UK visa sponsored tech jobs
# ============================================================
# What this script does:
# 1. Searches Adzuna for tech jobs in the UK
# 2. Filters by £41,700 visa salary threshold
# 3. Checks if company is on gov.uk sponsor list
# ============================================================

import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")       # from developer.adzuna.com
APP_KEY = os.getenv("ADZUNA_APP_KEY")     # from developer.adzuna.com
SPONSOR_CSV = "sponsor_list.csv"     # filename of gov.uk CSV in same folder
SALARY_THRESHOLD = 41700             # current skilled worker visa threshold
JOB_SEARCH = "cloud engineer"        # what job you are searching for

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
# STEP 3 - Search Adzuna for jobs
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
# STEP 4 - Filter jobs by salary and sponsorship
# ============================================================

qualifying_jobs = []

for job in data["results"]:

    title = job["title"]
    company = job["company"]["display_name"]
    location = job["location"]["display_name"]
    link = job["redirect_url"]
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

    # Passed both checks - add to list
    if salary_min is None:
        salary_display = "Salary not listed"
    else:
        salary_display = f"£{int(salary_min):,} - £{int(salary_max):,}"

    qualifying_jobs.append({
        "title": title,
        "company": company,
        "location": location,
        "salary": salary_display,
        "link": link
    })

    print(f"✓ GOOD MATCH | {title} at {company} | {salary_display}")

# ============================================================
# STEP 5 - Print the final results
# ============================================================

print("-" * 50)
print(f"\n✅ {len(qualifying_jobs)} jobs passed all checks:\n")

for i, job in enumerate(qualifying_jobs, 1):
    print(f"Job {i}:")
    print(f"  Title:    {job['title']}")
    print(f"  Company:  {job['company']}")
    print(f"  Location: {job['location']}")
    print(f"  Salary:   {job['salary']}")
    print(f"  Link:     {job['link']}")
    print()