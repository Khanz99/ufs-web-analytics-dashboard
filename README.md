# UFS Web Analytics Dashboard

Internal analytics dashboard for monitoring University of the Free State web performance using:

- Google Analytics 4 (GA4)
- Google Search Console
- Google Trends / SerpApi

---

# Features

- Automated dashboard refresh
- Daily scheduled updates
- Manual refresh button
- Device breakdown
- Top pages
- Top web stories
- Search trends
- Search Console queries
- Interactive charts

---

# Technologies Used

- HTML
- CSS
- JavaScript
- Python
- Flask
- Chart.js

---

# Project Structure

```text
CSS/
JS/
assets/
data/
debug/
scripts/
index.html
server.py
run_ga4_update.bat
requirements.txt
```

---

# Installation

## 1. Clone repository

```bash
git clone https://github.com/Khanz99/ufs-web-analytics-dashboard.git
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

# Credentials

The following credential files are required locally and are intentionally excluded from GitHub:

```text
scripts/service-account.json
scripts/search_console_credentials.json
scripts/search_console_token.json
```

---

# Running the Dashboard

## Start Flask server

```bash
python server.py
```

Dashboard will run at:

```text
http://127.0.0.1:5000
```

---

# Automated Updates

The dashboard uses:

```text
run_ga4_update.bat
```

to refresh dashboard data automatically.

Scheduled via Windows Task Scheduler:

- 07:45 daily
- 15:30 daily

---

# Manual Refresh

The dashboard includes a Refresh Data button that triggers:

```text
POST /refresh-data
```

which runs:

```text
scripts/update_dashboard_data.py
```

and reloads dashboard JSON data.

---

# Notes

- Credential files are excluded from GitHub using `.gitignore`
- Designed for internal institutional hosting
- Intended for deployment on UFS internal infrastructure / PIWI environment