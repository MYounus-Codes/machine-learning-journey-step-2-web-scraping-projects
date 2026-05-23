# Web Scraping Projects

This repository collects small web-scraping projects and utilities used to extract job data from sites (example: We Work Remotely). The primary, active project in this workspace is the advanced WWR scraper located in `advance-projects/project-1`.

**What’s included**
- `advance-projects/project-1/advance-version.py` — advanced We Work Remotely scraper (listing + detail scraping, CSV output)
- `advance-projects/project-1/jobs-scraper.py` — older/basic scraper sample
- `advance-projects/project-1/main-jobs.html` — saved listing-page sample (for offline selector testing)
- `advance-projects/project-1/one-job.html` — saved job-detail sample (for offline selector testing)
- `advance-projects/project-1/weworkremotely_jobs.csv` — last generated CSV output
- other example projects (basic/intermidiate folders) contain smaller scrapers for practice and demos

**Goals**
- Extract structured job data (title, company, post-date, type, region, description, skills, apply URL) from We Work Remotely.
- Save clean CSV output suitable for spreadsheet import or further processing.
- Provide offline HTML samples so selectors can be verified without live requests.

**Requirements**
- Python 3.10+ (project tested with Python 3.12.10)
- Dependencies: `requests`, `beautifulsoup4` (these are listed in `pyproject.toml`)

Quick environment setup (recommended):

1. Create a virtual environment (if you don't already have one):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies (from this workspace):

```powershell
python -m pip install -U pip
python -m pip install requests beautifulsoup4
```

If you prefer `pyproject.toml` tooling, use your chosen tool (poetry, pip-tools) to install the declared dependencies.

**How to run the advanced WeWorkRemotely scraper**

1. Activate your environment (see above).
2. From the project folder, run:

```powershell
cd advance-projects\project-1
python advance-version.py
```

- The script writes `weworkremotely_jobs.csv` into the same folder.
- The CSV writer now emits fully-quoted rows to handle commas and long description text safely.

**Offline selector testing (fast, no network)**

You can validate selectors against the provided sample HTML files without running the live scrape. Example Python snippet used during development:

```python
from pathlib import Path
from bs4 import BeautifulSoup
import importlib.util

spec = importlib.util.spec_from_file_location('advance', 'advance-projects/project-1/advance-version.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

listing = Path('advance-projects/project-1/main-jobs.html').read_text(encoding='utf-8')
job = Path('advance-projects/project-1/one-job.html').read_text(encoding='utf-8')

lsoup = BeautifulSoup(listing, 'html.parser')
jsoup = BeautifulSoup(job, 'html.parser')

print('links:', len(mod.extract_job_links(lsoup)))
print('sample details:', mod.parse_job_details(jsoup, 'https://example.com/sample'))
```

**CSV notes and GitHub preview**

- The scraper writes `advance-projects/project-1/weworkremotely_jobs.csv` with `csv.QUOTE_ALL` and UNIX line endings. This protects commas in titles/descriptions.
- GitHub's CSV viewer can render large files as raw text (especially when description fields are very long). That is a viewer limitation — the CSV itself is valid and opens correctly in Excel, LibreOffice, or Pandas.

**Troubleshooting & Tips**
- If you see unexpected fields or missing data, verify selectors by loading `one-job.html` and `main-jobs.html` locally and using the offline snippet above.
- To reduce GitHub preview noise, consider splitting long `job_description` into a separate file or storing only a truncated summary in the main CSV.
- Respect target site robots and rate limits. The scraper includes a polite sleep between requests (`time.sleep(1.5)`), but you should always confirm scraping permissions for production use.

**Project structure (high level)**

```
.
├─ advance-projects/
│  └─ project-1/
│     ├─ advance-version.py
│     ├─ jobs-scraper.py
│     ├─ main-jobs.html
│     ├─ one-job.html
│     └─ weworkremotely_jobs.csv
├─ basic-projects/
├─ intermidiate-projects/
├─ pyproject.toml
└─ README.md
```

**Next steps (optional)**
- Add unit tests for parsing functions (e.g., `parse_job_details` and `extract_job_links`).
- Add a small CLI wrapper that supports `--local` to parse local HTML fixtures only.
- Add a GitHub Action to regenerate a trimmed CSV or JSONL artifact for easy preview.

If you want, I can add a short `CONTRIBUTING.md` or a test harness next — which would you prefer?

***
Generated on 2026-05-23 — update this README as the project evolves.
