import json
from datetime import date, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ----------------------------
# Configuration
# ----------------------------
SITE_URL = "https://www.ufs.ac.za/"
SEARCH_TYPE = "web"
END_DATE = date.today() - timedelta(days=3)
START_DATE = END_DATE - timedelta(days=27)
ROW_LIMIT = 10

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCRIPT_DIR = Path(__file__).resolve().parent

OUTPUT_FILE = DATA_DIR / "search_console.json"
CREDENTIALS_FILE = SCRIPT_DIR / "search_console_credentials.json"
TOKEN_FILE = SCRIPT_DIR / "search_console_token.json"

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


# ----------------------------
# Helpers
# ----------------------------
def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def write_json(payload):
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_credentials():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                f"Missing OAuth credentials file: {CREDENTIALS_FILE}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES
        )
        creds = flow.run_local_server(port=0)

        with TOKEN_FILE.open("w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds


def build_service():
    creds = load_credentials()
    return build("searchconsole", "v1", credentials=creds)


def fetch_top_queries(service):
    request = {
        "startDate": START_DATE.isoformat(),
        "endDate": END_DATE.isoformat(),
        "dimensions": ["query"],
        "rowLimit": ROW_LIMIT,
        "dataState": "final",
        "type": SEARCH_TYPE,
    }

    response = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body=request
    ).execute()

    rows = response.get("rows", [])
    results = []

    for row in rows:
        keys = row.get("keys", [])
        query = keys[0].strip() if keys else ""
        clicks = int(round(row.get("clicks", 0)))

        if not query:
            continue

        results.append({
            "query": query,
            "clicks": clicks
        })

    results.sort(key=lambda x: x["clicks"], reverse=True)
    return results


# ----------------------------
# Main
# ----------------------------
def main():
    ensure_dirs()
    service = build_service()
    queries = fetch_top_queries(service)

    payload = {
        "queries": queries
    }

    write_json(payload)
    print(f"Search Console JSON written to: {OUTPUT_FILE}")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()