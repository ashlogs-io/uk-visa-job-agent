# 🤖 UK Visa Sponsored Job Agent

An AI-powered job hunting agent built in Python that automatically finds, filters, and analyses UK tech job listings — specifically targeting roles that offer visa sponsorship under the Skilled Worker visa scheme.

---

## What It Does

Finding visa-sponsored tech jobs in the UK manually is time-consuming — you have to search job boards, cross-reference the government's licensed sponsor register, check salary thresholds, and write tailored cover letters for every application. This agent automates the entire process.

```
Searches Adzuna for UK tech jobs
         ↓
Filters by £41,700 Skilled Worker visa salary threshold
         ↓
Cross-references gov.uk licensed sponsor register (140,000+ companies)
         ↓
Claude AI analyses each qualifying job and scores it 1-10
         ↓
Generates a tailored cover letter for every job scoring 5+
         ↓
Saves cover letters as text files — ready to send
```

---

## Example Output

```
Loading sponsor list...
Loaded 140881 licensed sponsors

Searching for: cloud engineer
Salary threshold: £41,700

Adzuna found 2241 total jobs
Checking first 10...

X NOT ON SPONSOR LIST | Cloud Engineer at Spectrum IT Recruitment
X SALARY TOO LOW      | M365 Cloud Engineer at Reed | £35,000

✓ PASSED FILTERS | Azure Cloud Engineer at Noir | £45,000 - £75,000
  Analysing role with Claude...
  Score: 6/10
  Generating cover letter...
  Cover letter saved: cover_letters/Azure_Cloud_Engineer_Noir.txt

✓ PASSED FILTERS | Azure Cloud Engineer at COMPUTACENTER | £57,818
  Analysing role with Claude...
  Score: 7/10
  Generating cover letter...
  Cover letter saved: cover_letters/Azure_Cloud_Engineer_COMPUTACENTER.txt

✅ 2 cover letters saved to the cover_letters/ folder
```

---

## Tech Stack

- **Python** — core language
- **Anthropic Claude API** — job analysis and cover letter generation
- **Adzuna Jobs API** — UK job listings
- **pandas** — processing the gov.uk sponsor register CSV
- **python-dotenv** — secure environment variable management

---

## How It Works

### 1. Job Search
Uses the Adzuna API to search for tech roles across the UK. The search term, salary threshold, and number of results are all configurable.

### 2. Salary Filter
Automatically skips any role where the advertised salary falls below the current Skilled Worker visa threshold of £41,700. Roles with no salary listed are kept and flagged for manual review.

### 3. Sponsor Check
Downloads and searches the official UK government register of licensed visa sponsors. Company names are cleaned and normalised before matching to handle variations like "Computacenter LIMITED" vs "Computacenter (UK) Ltd".

### 4. AI Analysis
Each qualifying job is sent to Claude AI along with the candidate's profile. Claude returns a structured response including a score out of 10, a verdict, key reasons the role is a good or poor fit, and any red flags to watch out for.

### 5. Cover Letter Generation
For any job scoring 5 or above, Claude generates a tailored cover letter based on the specific job description and candidate profile. Letters are saved as individual text files in a `cover_letters/` folder.

---

## Setup

### Prerequisites
- Python 3.8 or higher
- An [Adzuna API account](https://developer.adzuna.com) (free)
- An [Anthropic API account](https://console.anthropic.com) (paid, ~$5 lasts weeks)
- The [gov.uk licensed sponsor CSV](https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers) (free download)

### Installation

Clone the repository:
```bash
git clone https://github.com/ashlogs-io/uk-visa-job-agent
cd uk-visa-job-agent
```

Install dependencies:
```bash
pip install requests pandas anthropic python-dotenv
```

Create a `.env` file in the project root:
```
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
ANTHROPIC_API_KEY=your_anthropic_api_key
YOUR_NAME=Your Full Name
JOB_SEARCH=cloud engineer
```

Download the gov.uk sponsor list CSV and save it in the project folder as `sponsor_list.csv`.

### Run

```bash
python3 job_agent.py
```

Cover letters will be saved to the `cover_letters/` folder.

---

## Configuration

All configuration is handled through the `.env` file and the constants at the top of `job_agent.py`:

| Variable | Description | Default |
|---|---|---|
| `JOB_SEARCH` | Job title to search for | `cloud engineer` |
| `SALARY_THRESHOLD` | Minimum salary in £ | `41700` |
| `COVER_LETTER_THRESHOLD` | Minimum AI score to generate letter | `5` |
| `YOUR_NAME` | Your name for cover letters | from `.env` |

---

## Project Structure

```
uk-visa-job-agent/
│
├── job_agent.py          # Main agent script
├── sponsor_list.csv      # gov.uk licensed sponsor register (not in repo)
├── cover_letters/        # Generated cover letters (not in repo)
├── .env                  # API keys and personal details (not in repo)
├── .gitignore            # Keeps secrets and outputs out of GitHub
└── README.md             # This file
```

---

## Why I Built This

As an international graduate on a Skilled Worker visa, finding UK tech roles that offer visa sponsorship and meet the salary threshold involves a lot of manual filtering. I built this agent to automate that process — and in doing so, gained hands-on experience with Python, REST APIs, AI integration, and data processing.

This project is part of my broader journey transitioning from support work into cloud engineering and IT infrastructure.

---

## Roadmap

- [ ] Email daily summary of new matches
- [ ] SQLite database to track applications and avoid duplicates
- [ ] Search multiple job titles simultaneously
- [ ] Deploy to Azure Functions to run automatically every morning
- [ ] Add Reed.co.uk as a second job source

---

## Important Notes

- This agent is for personal use only
- Always review AI-generated cover letters before sending — personalise them
- The gov.uk sponsor list should be re-downloaded regularly as it updates weekly
- Adzuna free tier allows 250 API calls per day

---

## Author

Built by a CS graduate navigating the UK tech job market as an international candidate.