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


# Minimun AI score to generat a cover letter for
# Jobs scoring below this are not worth applying to
COVER_LETTER_THRESHOLD = 5

# My full name and this will appear in the cover letter
MY_NAME = os.getenv("MY_NAME")

# MY profie - Claude uses this to score each job
MY_PROFILE = """
BACKGROUND:
- BSc Computer Science, graduated 2024, UK university
- Currently working as Senior Support Worker in care sector
- Did 1 year placement during my degree at Oracle as Site Reliability Engineer Intern
- Some experience in computer network from internships
- No commercial tech experience yet
- Age 32, career changer into tech

VISA:
- Currently on Skilled Worker visa
- Needs employer to be a licensed UK visa sponsor
- Needs new Certificate of Sponsorship to switch roles

SKILLS I ACTUALLY HAVE:
- Networking concepts (from degree and internships) - TCP/IP, DNS, subnets
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
# STEP 4 - Claude cover letter generator function
# ============================================================

def generate_cover_letter(title, company, location, salary, description):

    print(f" Generating cover letter...")

    message = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system="""
        You are an expert UK job application writer.
        Write professional, genuine cover letters that sound human - not generic or robotic.

        Rules:
        - 3 paragraphs only
        - UK English spelling throughout
        - Naturally mention visa sponsorship requirement in the final paragraph
        - Do not fabricate experience the candidate does not have
        - Be honest about being a career changer - frame it as a strength
        - DO not use cliches like "I am writing to apply" or "I am a hard worker"
        - Address it as: Dear Hiring Manager
        - Sign off with the candidate's name
        """,
        messages=[
            {
                "role": "user",
                "content": f"""
                Write a cover letter for this job application:

                CANDIDATE PROFILE:
                {MY_PROFILE}

                CANDIDATE NAME: {MY_NAME}

                JOB DETAILS:
                Title: {title}
                Company: {company}
                Location: {location}
                Salary: {salary}
                Description: {description[:1500]}

                Write a tailored, honest cover letter for this specific role.
                """
            }
        ]
    )

    return message.content[0].text

# ============================================================
# STEP 5 - Helper to extract score from analysis text
# ============================================================
def extract_score(analysis_text):
    #Looks for "SCORE: 7" in Claude's response and returns 7
    for line in analysis_text.split("\n"):
        if line.strip().startswith("SCORE:"):
            try:
                score = int(line.split(":")[1].strip().split("/")[0])
                return score
            except:
                return 0
    return 0

# ============================================================
# STEP 6 - Create a folder to save cover letters
# ============================================================

output_folder = "cover_letters"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"Created folder: {output_folder}/\n")

# ============================================================
# STEP 7 - Search Adzuna for jobs
# ============================================================

print(f"Searching for: {JOB_SEARCH}")
print(f"Salary threshold: £{SALARY_THRESHOLD:,}\n")
print(f"Cover letter threshold: Score {COVER_LETTER_THRESHOLD}+\n")

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
# STEP 5 - Filter jobs by salary and sponsorship, analyse and generate cover letters
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
    # Extract the numeric score from the analysis
    score = extract_score(ai_analysis)
    print(f" Score: {score}/10")

    # Generate cover letter only if score if good enough
    cover_letter = None

    if score >= COVER_LETTER_THRESHOLD:
        cover_letter = generate_cover_letter(
            title, company, location, salary_display, description
        )
        
        # Save cover letter as a text file
        safe_company = company.replace (" ", "_").replace("/", "-")[:30]
        safe_title = title.replace(" ", "_").replace("/", "-")[:30]
        filename = f"{output_folder}/{safe_title}_{safe_company}.text"

        with open(filename, "w") as f:
            f.write(f"Job: {title}\n")
            f.write(f"Company: {company}\n")
            f.write(f"Location: {location}\n")
            f.write(f"Salary: {salary_display}\n")
            f.write(f"Link: {link}\n")
            f.write(f"AI Score: {score}/10\n")
            f.write("\n" + "=" * 50 + "\n\n")
            f.write(cover_letter)

        print(f" Cover letter saved: {filename}")

    else:
        print(f" Score too low ({score}/10) - skipping cover letter")

    qualifying_jobs.append({
        "title": title,
        "company": company,
        "location": location,
        "salary": salary_display,
        "link": link,
        "score": score,
        "ai_analysis": ai_analysis,
        "cover_letter": cover_letter
    })

# ============================================================
# STEP 6 - Print the final results summary
# ============================================================

print("\n")
print("-" * 50)
print(f"RESULTS: {len(qualifying_jobs)} jobs passed all checks")
print("=" * 50)

for i, job in enumerate(qualifying_jobs, 1):
    print(f"Job {i}:")
    print(f"  Title:    {job['title']}")
    print(f"  Company:  {job['company']}")
    print(f"  Location: {job['location']}")
    print(f"  Salary:   {job['salary']}")
    print(f"  Link:     {job['link']}")
    print(f"\n AI Anlysis:")
    print(f" {job['ai_analysis']}")
    if job['cover_letter']:
        print(f"\n Cover letter saved to cover_letters folder")
    print("-" * 50)

# Summary at the end
letters_generated = sum(1 for j in qualifying_jobs if j['cover_letter'])
print(f"\n✅ {letters_generated} cover letters saved to the cover_letters/ folder")
print(f" Open them, personalised if needed, then apply!  \n")