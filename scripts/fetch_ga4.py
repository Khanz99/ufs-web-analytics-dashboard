import json
import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    FilterExpression,
    Metric,
    OrderBy,
    RunReportRequest,
)
from google.oauth2 import service_account


# ----------------------------
# Configuration
# ----------------------------
PROPERTY_ID = "395126815"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

SERVICE_ACCOUNT_FILE = BASE_DIR / "scripts" / "service-account.json"

WEB_STORIES_PREFIX = os.getenv("GA4_WEB_STORIES_PREFIX", "").strip()

START_DATE = os.getenv("GA4_START_DATE", "7daysAgo")
END_DATE = os.getenv("GA4_END_DATE", "yesterday")


# ----------------------------
# Helpers
# ----------------------------
def ensure_config() -> None:
    if not PROPERTY_ID:
        raise ValueError("Missing GA4 property ID.")

    if not SERVICE_ACCOUNT_FILE.exists():
        raise FileNotFoundError(
            f"Service account file not found: {SERVICE_ACCOUNT_FILE}"
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)


def client() -> BetaAnalyticsDataClient:
    credentials = service_account.Credentials.from_service_account_file(
        str(SERVICE_ACCOUNT_FILE)
    )
    return BetaAnalyticsDataClient(credentials=credentials)


def property_name() -> str:
    return f"properties/{PROPERTY_ID}"


def seconds_to_hhmmss(seconds_value: float | int | str) -> str:
    try:
        total_seconds = int(round(float(seconds_value)))
    except (TypeError, ValueError):
        total_seconds = 0

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def write_json(filename: str, payload) -> None:
    path = DATA_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def resolve_ga4_date(date_str: str) -> str:
    today = datetime.now().date()

    if date_str == "today":
        return today.isoformat()
    if date_str == "yesterday":
        return (today - timedelta(days=1)).isoformat()

    if date_str.endswith("daysAgo"):
        try:
            days = int(date_str.replace("daysAgo", ""))
            return (today - timedelta(days=days)).isoformat()
        except ValueError:
            pass

    return date_str


def format_reporting_period(start_date: str, end_date: str) -> str:
    resolved_start = resolve_ga4_date(start_date)
    resolved_end = resolve_ga4_date(end_date)

    try:
        start_obj = datetime.strptime(resolved_start, "%Y-%m-%d")
        end_obj = datetime.strptime(resolved_end, "%Y-%m-%d")
        start_label = start_obj.strftime("%b %d, %Y").replace(" 0", " ")
        end_label = end_obj.strftime("%b %d, %Y").replace(" 0", " ")
        return f"{start_label} - {end_label}"
    except ValueError:
        return f"{resolved_start} - {resolved_end}"


def run_report(
    ga_client: BetaAnalyticsDataClient,
    *,
    dimensions: List[str],
    metrics: List[str],
    limit: int = 100,
    order_bys: List[OrderBy] | None = None,
    dimension_filter: FilterExpression | None = None,
):
    request = RunReportRequest(
        property=property_name(),
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=START_DATE, end_date=END_DATE)],
        limit=limit,
        order_bys=order_bys or [],
        dimension_filter=dimension_filter,
    )
    return ga_client.run_report(request)


def get_metric_value(row, index: int = 0) -> str:
    return row.metric_values[index].value


def get_dimension_value(row, index: int = 0) -> str:
    return row.dimension_values[index].value


# ----------------------------
# Fetch blocks
# ----------------------------
def fetch_total_page_views(ga_client: BetaAnalyticsDataClient) -> int:
    response = run_report(
        ga_client,
        dimensions=[],
        metrics=["screenPageViews"],
        limit=1,
    )

    if not response.rows:
        return 0

    return int(float(get_metric_value(response.rows[0], 0)))


def fetch_overview(ga_client: BetaAnalyticsDataClient) -> Dict:
    response = run_report(
        ga_client,
        dimensions=[],
        metrics=["activeUsers", "userEngagementDuration", "newUsers"],
        limit=1,
    )

    if not response.rows:
        return {
            "users": 0,
            "page_views": 0,
            "avg_engagement_time": "00:00:00",
            "new_users": 0,
            "returning_users": 0,
            "new_users_percent": 0,
            "returning_users_percent": 0,
            "report_period": format_reporting_period(START_DATE, END_DATE),
        }

    row = response.rows[0]
    users = int(float(get_metric_value(row, 0)))
    total_engagement_duration = float(get_metric_value(row, 1))
    new_users = int(float(get_metric_value(row, 2)))

    page_views = fetch_total_page_views(ga_client)

    avg_engagement_per_active_user = (
        total_engagement_duration / users if users else 0
    )

    returning_users = max(0, users - new_users)

    return {
        "users": users,
        "page_views": page_views,
        "avg_engagement_time": seconds_to_hhmmss(avg_engagement_per_active_user),
        "new_users": new_users,
        "returning_users": returning_users,
        "new_users_percent": round((new_users / users) * 100, 1) if users else 0,
        "returning_users_percent": round((returning_users / users) * 100, 1) if users else 0,
        "report_period": format_reporting_period(START_DATE, END_DATE),
    }


def fetch_daily_traffic(ga_client: BetaAnalyticsDataClient) -> List[Dict]:
    response = run_report(
        ga_client,
        dimensions=["date"],
        metrics=["activeUsers"],
        limit=31,
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
    )

    items = []
    for row in response.rows:
        raw_date = get_dimension_value(row, 0)
        formatted = f"{raw_date[6:8]} {month_name(raw_date[4:6])}"
        items.append(
            {
                "date": formatted,
                "active_users": int(float(get_metric_value(row, 0))),
            }
        )

    return items


def fetch_device_breakdown(ga_client: BetaAnalyticsDataClient) -> List[Dict]:
    response = run_report(
        ga_client,
        dimensions=["deviceCategory"],
        metrics=["activeUsers"],
        limit=10,
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)
        ],
    )

    raw_items = []

    for row in response.rows:
        device = get_dimension_value(row, 0)

        if device.lower().strip() == "smart tv":
            continue

        users = int(float(get_metric_value(row, 0)))
        raw_items.append({"device": device, "users": users})

    total = sum(item["users"] for item in raw_items) or 1

    items = []

    for item in raw_items:
        items.append(
            {
                "device": item["device"],
                "percentage": round((item["users"] / total) * 100, 1),
            }
        )

    return items


def fetch_top_pages(ga_client: BetaAnalyticsDataClient) -> List[Dict]:
    response = run_report(
        ga_client,
        dimensions=["unifiedPagePathScreen"],
        metrics=["screenPageViews"],
        limit=10,
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
        ],
    )

    items = []

    for row in response.rows:
        page = get_dimension_value(row, 0) or "/"
        visits = int(float(get_metric_value(row, 0)))
        items.append({"page": page, "visits": visits})

    return items


def fetch_top_web_stories(ga_client: BetaAnalyticsDataClient) -> List[Dict]:
    response = run_report(
        ga_client,
        dimensions=["pagePath"],
        metrics=["screenPageViews"],
        limit=100,
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
        ],
    )

    items = []
    seen_titles = set()

    for row in response.rows:
        path = get_dimension_value(row, 0) or "/"
        views = int(float(get_metric_value(row, 0)))

        if not is_current_year_news_article(path):
            continue

        title = slug_to_title(path)

        if not title:
            continue

        if title.lower() in seen_titles:
            continue

        seen_titles.add(title.lower())

        items.append(
            {
                "title": title,
                "page_views": views,
            }
        )

        if len(items) == 5:
            break

    return items


def fetch_new_vs_returning(ga_client: BetaAnalyticsDataClient) -> Dict[str, int]:
    response = run_report(
        ga_client,
        dimensions=["newVsReturning"],
        metrics=["activeUsers"],
        limit=10,
    )

    result = {"new": 0, "returning": 0}

    for row in response.rows:
        bucket = get_dimension_value(row, 0).lower()
        value = int(float(get_metric_value(row, 0)))

        if bucket in result:
            result[bucket] = value

    return result


# ----------------------------
# Utilities
# ----------------------------
def month_name(mm: str) -> str:
    months = {
        "01": "Jan",
        "02": "Feb",
        "03": "Mar",
        "04": "Apr",
        "05": "May",
        "06": "Jun",
        "07": "Jul",
        "08": "Aug",
        "09": "Sep",
        "10": "Oct",
        "11": "Nov",
        "12": "Dec",
    }

    return months.get(mm, mm)


def current_year() -> str:
    return str(datetime.now().year)


def is_current_year_news_article(path: str) -> bool:
    if not path:
        return False

    path_lower = path.lower().rstrip("/")
    year = current_year()

    return (
        f"/{year}/" in path_lower
        and "news" in path_lower
        and path_lower != "/"
    )


def is_valid_article_slug(slug: str) -> bool:
    if not slug:
        return False

    invalid_slugs = {
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
        "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
        "news", "campus-news", "archive", "news-archive", "item",
    }

    slug_lower = slug.lower().strip()

    if slug_lower in invalid_slugs:
        return False

    if slug_lower.isdigit():
        return False

    if len(slug_lower) < 4:
        return False

    return True


def slug_to_title(path: str) -> str | None:
    if not path or path == "/":
        return None

    slug = path.rstrip("/").split("/")[-1].strip()

    if not is_valid_article_slug(slug):
        return None

    slug = slug.replace("-", " ").strip()

    if not slug:
        return None

    return slug.capitalize()


# ----------------------------
# Main
# ----------------------------
def  main() -> None:
    ensure_config()
    ga_client = client()

    overview = fetch_overview(ga_client)
   
    
    daily_traffic = fetch_daily_traffic(ga_client)
    device_breakdown = fetch_device_breakdown(ga_client)
    top_pages = fetch_top_pages(ga_client)
    top_web_stories = fetch_top_web_stories(ga_client)

    write_json("overview.json", overview)
    write_json("daily_traffic.json", daily_traffic)
    write_json("device_breakdown.json", device_breakdown)
    write_json("top_pages.json", top_pages)
    write_json("top_web_stories.json", top_web_stories)

    print(f"Writing files to: {DATA_DIR}")
    print("GA4 dashboard JSON files updated successfully.")


if __name__ == "__main__":
    main()