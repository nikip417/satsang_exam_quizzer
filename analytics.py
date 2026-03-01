"""
Analytics: total subscribers per channel and average quiz responses per exam per day.

- Fetches current subscriber/member count for each channel via the bot.
- Reads historical_poll_log.csv, groups by exam and date (day), and writes
  CSVs plus a styled HTML report (subscribers, week-over-week graphs, responses by day).
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from telegram import Bot  # type: ignore

from quizzer import bot_token, telegram_chat_info

HISTORICAL_POLL_LOG_FILE = Path("2026 results/historical_poll_log.csv")
AVG_RESPONSES_BY_DAY_FILE = Path("2026 results/analytics_avg_responses_by_day.csv")
SUBSCRIBER_COUNTS_FILE = Path("2026 results/analytics_subscriber_counts.csv")
REPORT_HTML_FILE = Path("2026 results/analytics_report.html")
COLUMNS = ["exam_name", "chat_id", "message_id", "question", "date", "total_voters"]


async def get_subscriber_counts(bot: Bot) -> dict[str, int]:
    """Return {exam_name: member_count} for each configured chat."""
    counts = {}
    for exam_name, chat_id in telegram_chat_info.items():
        n = await bot.get_chat_member_count(chat_id=chat_id)
        counts[exam_name] = n
    return counts


def load_historical_poll_log() -> pd.DataFrame:
    """Load historical poll log; handle missing header."""
    if not HISTORICAL_POLL_LOG_FILE.exists():
        return pd.DataFrame(columns=COLUMNS)

    df = pd.read_csv(
        HISTORICAL_POLL_LOG_FILE,
        names=COLUMNS,
        header=None,
        encoding="utf-8",
    )
    # If first row is the header, drop it and use it as column names
    if len(df) > 0 and df.iloc[0]["exam_name"] == "exam_name":
        df = df.iloc[1:].reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df["total_voters"] = pd.to_numeric(df["total_voters"], errors="coerce").fillna(0).astype(int)
    df = df.dropna(subset=["date"])
    return df


def _first_monday(year: int) -> datetime:
    jan_1 = datetime(year, 1, 1)
    days_until_monday = (7 - jan_1.weekday()) % 7
    if days_until_monday == 0 and jan_1.weekday() != 0:
        days_until_monday = 7
    return jan_1 + timedelta(days=days_until_monday)


def _quiz_week_index(dt: datetime) -> tuple[int, int]:
    """Return (year, week_index) for quiz schedule (week 0 = first Monday of Jan)."""
    year = dt.year
    first_monday = _first_monday(year)
    if dt < first_monday:
        year -= 1
        first_monday = _first_monday(year)
    week_index = (dt - first_monday).days // 7
    return year, week_index


def average_responses_by_exam_and_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group by exam_name and date (day); return mean total_voters and poll count per day.
    """
    if df.empty:
        return pd.DataFrame(columns=["exam_name", "date", "avg_quiz_responses", "polls_count"])

    df = df.copy()
    df["date_only"] = df["date"].dt.date

    grouped = (
        df.groupby(["exam_name", "date_only"], as_index=False)
        .agg(
            avg_quiz_responses=("total_voters", "mean"),
            polls_count=("message_id", "count"),
        )
    )
    grouped["avg_quiz_responses"] = grouped["avg_quiz_responses"].round(1)
    grouped = grouped.rename(columns={"date_only": "date"})
    return grouped.sort_values(["exam_name", "date"])


def average_responses_by_exam_and_week(by_day: pd.DataFrame) -> pd.DataFrame:
    """Aggregate by-day data into week-over-week (quiz weeks: first Monday of Jan = week 0)."""
    if by_day.empty:
        return pd.DataFrame(
            columns=["exam_name", "year", "week_index", "week_label", "avg_quiz_responses", "polls_count"]
        )

    by_day = by_day.copy()
    by_day["date_dt"] = pd.to_datetime(by_day["date"])
    by_day["year"] = by_day["date_dt"].apply(lambda d: _quiz_week_index(d.to_pydatetime())[0])
    by_day["week_index"] = by_day["date_dt"].apply(lambda d: _quiz_week_index(d.to_pydatetime())[1])

    grouped = (
        by_day.groupby(["exam_name", "year", "week_index"], as_index=False)
        .agg(
            avg_quiz_responses=("avg_quiz_responses", "mean"),
            polls_count=("polls_count", "sum"),
        )
    )
    grouped["avg_quiz_responses"] = grouped["avg_quiz_responses"].round(1)

    def week_label(row: pd.Series) -> str:
        y, w = int(row["year"]), int(row["week_index"])
        start = _first_monday(y) + timedelta(weeks=w)
        end = start + timedelta(days=6)
        return f"W{w + 1} ({start.strftime('%b %d')}–{end.strftime('%b %d')})"

    grouped["week_label"] = grouped.apply(week_label, axis=1)
    return grouped.sort_values(["exam_name", "year", "week_index"])


def write_subscriber_counts_csv(counts: dict[str, int]) -> None:
    """Write subscriber counts to CSV (exam_name, subscriber_count)."""
    rows = [{"exam_name": name, "subscriber_count": count} for name, count in counts.items()]
    pd.DataFrame(rows).to_csv(SUBSCRIBER_COUNTS_FILE, index=False)


def _build_chart_data(by_week: pd.DataFrame) -> dict:
    """Build Chart.js-friendly data: labels (week labels) and datasets (one per exam)."""
    if by_week.empty:
        return {"labels": [], "datasets": []}

    # Unique weeks in order (year, week_index)
    weeks = by_week[["year", "week_index", "week_label"]].drop_duplicates()
    weeks = weeks.sort_values(["year", "week_index"])
    labels = weeks["week_label"].tolist()
    week_keys = list(zip(weeks["year"], weeks["week_index"]))

    colors = ["#3498db", "#2ecc71", "#e74c3c", "#9b59b6"]  # blue, green, red, purple
    datasets = []

    for i, exam_name in enumerate(telegram_chat_info):
        subset = by_week[by_week["exam_name"] == exam_name]
        value_by_week = dict(zip(zip(subset["year"], subset["week_index"]), subset["avg_quiz_responses"]))
        data = [float(value_by_week[k]) if k in value_by_week and pd.notna(value_by_week[k]) else None for k in week_keys]
        color = colors[i % len(colors)]
        datasets.append({
            "label": exam_name.capitalize(),
            "data": data,
            "borderColor": color,
            "backgroundColor": color + "20",
            "tension": 0.2,
            "fill": False,
        })

    return {"labels": labels, "datasets": datasets}


def write_html_report(counts: dict[str, int], by_day: pd.DataFrame) -> None:
    """Write a styled HTML report with subscribers, week-over-week graphs, and responses by day."""
    total_subs = sum(counts.get(n, 0) for n in telegram_chat_info)
    report_date = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

    # Week-over-week aggregation and chart data
    by_week = average_responses_by_exam_and_week(by_day)
    chart_data = _build_chart_data(by_week)
    chart_data_json = json.dumps(chart_data)

    # Build subscriber cards HTML
    subscriber_cards = "".join(
        f"""
        <div class="card">
          <span class="card-label">{name}</span>
          <span class="card-value">{counts.get(name, 0):,}</span>
        </div>"""
        for name in telegram_chat_info
    )

    # Build table rows: group by exam for clearer display
    table_rows = []
    for exam_name in telegram_chat_info:
        subset = by_day[by_day["exam_name"] == exam_name]
        for _, row in subset.iterrows():
            date_str = str(row["date"]) if hasattr(row["date"], "isoformat") else row["date"]
            table_rows.append(
                f"""
        <tr>
          <td>{exam_name}</td>
          <td>{date_str}</td>
          <td class="num">{row['avg_quiz_responses']:,.1f}</td>
          <td class="num">{int(row['polls_count'])}</td>
        </tr>"""
            )
    table_body = "\n".join(table_rows) if table_rows else "<tr><td colspan='4'>No data</td></tr>"

    charts_section = ""
    if chart_data["labels"]:
        charts_section = """
    <section>
      <div class="section-title">Week-over-week: average quiz responses</div>
      <p class="chart-desc">Average responses per poll by quiz week (first Monday of January = Week 1).</p>
      <div class="chart-wrap">
        <canvas id="chartWeekOverWeek" aria-label="Week over week average quiz responses"></canvas>
      </div>
    </section>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Quiz Channel Analytics</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js" crossorigin="anonymous"></script>
  <style>
    :root {{
      --bg: #f8f9fa;
      --card-bg: #fff;
      --border: #dee2e6;
      --primary: #2c3e50;
      --accent: #3498db;
      --muted: #6c757d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: var(--bg);
      color: var(--primary);
      margin: 0;
      padding: 2rem;
      line-height: 1.5;
    }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.25rem; color: var(--primary); }}
    .meta {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 2rem; }}
    section {{ margin-bottom: 2rem; }}
    .section-title {{
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 1rem;
      color: var(--primary);
    }}
    .chart-desc {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 1rem; }}
    .chart-wrap {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
      position: relative;
      height: 320px;
    }}
    .cards {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem 1.5rem;
      min-width: 140px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }}
    .card-label {{ font-size: 0.85rem; color: var(--muted); text-transform: capitalize; }}
    .card-value {{ font-size: 1.5rem; font-weight: 600; color: var(--accent); }}
    .total-card .card-value {{ color: var(--primary); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--card-bg);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }}
    th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border); }}
    th {{
      background: var(--primary);
      color: #fff;
      font-weight: 600;
      font-size: 0.9rem;
    }}
    tr:hover {{ background: rgba(52, 152, 219, 0.06); }}
    .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Quiz Channel Analytics</h1>
    <p class="meta">Report generated on {report_date}</p>

    <section>
      <div class="section-title">Total subscribers per channel</div>
      <div class="cards">
        <div class="card total-card">
          <span class="card-label">Total (all channels)</span>
          <span class="card-value">{total_subs:,}</span>
        </div>
        {subscriber_cards}
      </div>
    </section>
{charts_section}

    <section>
      <div class="section-title">Average quiz responses per exam per day</div>
      <table>
        <thead>
          <tr>
            <th>Exam</th>
            <th>Date</th>
            <th class="num">Avg responses</th>
            <th class="num">Polls</th>
          </tr>
        </thead>
        <tbody>
{table_body}
        </tbody>
      </table>
    </section>
  </div>
  <script>
    (function () {{
      var chartData = {chart_data_json};
      if (chartData.labels.length === 0) return;
      var ctx = document.getElementById('chartWeekOverWeek');
      if (!ctx) return;
      new Chart(ctx.getContext('2d'), {{
        type: 'line',
        data: chartData,
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'top' }}
          }},
          scales: {{
            x: {{
              ticks: {{ maxRotation: 45, minRotation: 45, maxTicksLimit: 14 }}
            }},
            y: {{
              beginAtZero: true,
              title: {{ display: true, text: 'Avg responses' }}
            }}
          }}
        }}
      }});
    }})();
  </script>
</body>
</html>
"""
    REPORT_HTML_FILE.write_text(html, encoding="utf-8")


async def main() -> None:
    bot = Bot(token=bot_token)
    counts: dict[str, int] = {}

    # 1) Subscribers per channel → print, write CSV, and use in report
    print("=== Total subscribers (members) per channel ===\n")
    try:
        counts = await get_subscriber_counts(bot)
        for exam_name in telegram_chat_info:
            print(f"  {exam_name}: {counts.get(exam_name, 'N/A'):,}")
    except Exception as e:
        print(f"  Error fetching subscriber counts: {e}\n")
        counts = {name: 0 for name in telegram_chat_info}
    if counts:
        write_subscriber_counts_csv(counts)
        print(f"\nSubscriber counts written to {SUBSCRIBER_COUNTS_FILE}")

    # 2) Average quiz responses per exam per day → CSV + HTML report
    df = load_historical_poll_log()
    if df.empty:
        print("No data in historical_poll_log.csv (or file missing).")
        by_day = average_responses_by_exam_and_day(df)
    else:
        by_day = average_responses_by_exam_and_day(df)
        by_day.to_csv(AVG_RESPONSES_BY_DAY_FILE, index=False)
        print(f"Average quiz responses by day written to {AVG_RESPONSES_BY_DAY_FILE}")

    # 3) Styled HTML report (subscribers + responses table)
    write_html_report(counts, by_day)
    print(f"Report written to {REPORT_HTML_FILE} (open in a browser)")


if __name__ == "__main__":
    asyncio.run(main())
