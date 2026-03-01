# Satsang Exam Quizzes

This repo posts quiz questions to Telegram channels (Prarambh, Parichay, Pravesh, Pravin) on a fixed schedule and supports scraping poll data for analytics.

## Running the quizzer

### Via GitHub (current setup)

The quizzer is **run automatically via a GitHub Actions pipeline**:

- **Workflow:** [`.github/workflows/quiz_scheduler.yml`](.github/workflows/quiz_scheduler.yml)
- **Schedule:** Every **Monday and Thursday at 11:00 AM UTC**
- **Action:** The workflow checks out the repo, installs dependencies with `uv`, and runs `uv run python main.py`.

You can also trigger a run manually from the repo: **Actions → Quiz Scheduler → Run workflow**.

On each run, the pipeline:

1. Computes the current quiz number (1–14) from the calendar (first Monday of January = week 0, Mon/Thu quiz days).
2. Loads quiz data from the `master_quiz_doc_*.csv` files for that quiz number.
3. Posts each question as a Telegram quiz poll to the four exam channels.

### Running locally

If you need to run the quizzer on your machine (e.g. to test):

```bash
# Install dependencies (uv)
uv sync

# Post the current/next scheduled quiz to all four channels
uv run python main.py
```

Requires the bot token and channel IDs configured in `quizzer.py` (or via env/secrets if you add that).

---

## Gathering metrics before closing channels

After all 14 quiz days are over and before closing or archiving the channels, you should **gather metrics** (subscriber counts and poll engagement). That is done by **scraping the polls** from each channel and then running the analytics scripts.

### 1. Scrape historical polls (Telethon)

This walks each channel’s message history and records every quiz poll (message ID, date, total voters) into `historical_poll_log.csv`.

**One-time setup:**

- Get **API ID** and **API hash** from [my.telegram.org](https://my.telegram.org).
- Put them in `scrape_polls_telethon.py` (or use env vars if you add that).
- Install Telethon: `uv add telethon` (or `pip install telethon`).

**Run:**

```bash
uv run python scrape_polls_telethon.py
```

On first run you’ll be prompted for your phone number and login code. A session file is saved so you usually don’t need to log in again. The script writes/appends to `historical_poll_log.csv`.

### 2. Run analytics

Using the bot and (optionally) the scraped log, this script:

- Fetches **total subscriber count** per channel.
- Computes **average quiz responses per exam per day** from `historical_poll_log.csv`.
- Writes CSVs and a styled **HTML report** (`analytics_report.html`).

```bash
uv run python analytics.py
```

**Outputs:**

- `analytics_subscriber_counts.csv` — subscriber count per channel  
- `analytics_avg_responses_by_day.csv` — average responses per exam per day  
- `analytics_report.html` — open in a browser for a single-page summary (subscribers + table of engagement)

**Suggested workflow before closing channels:**

1. Run `scrape_polls_telethon.py` so all quiz polls are in `historical_poll_log.csv`.
2. Run `analytics.py` to get subscriber counts and engagement.
3. Save the report and CSVs (e.g. into a `2026 results/` or similar folder) for records.

---

## Other scripts

| Script | Purpose |
|--------|--------|
| `main.py` | Entry point used by the GitHub pipeline; posts the current quiz to all four channels. |
| `repost_parichay_prarambh.py` | Reposts **all** questions (quizzes 1–14) to **Parichay and Prarambh** only. |
| `test_repost_preview.py` | Prints a preview of formatted questions (no posting). Use `--all` to see every question. |

---

## Quiz schedule (reference)

- **14 quizzes** per year, numbered 1–14.
- **Quiz days:** Monday and Thursday, starting from the **first Monday of January** (week 0).
- Odd quiz numbers → Monday; even → Thursday.
- Each quiz has 7 questions; questions are numbered sequentially (e.g. Quiz 1 = 1–7, Quiz 2 = 8–14, …).

Quiz data lives in `master_quiz_doc_<exam>.csv` (e.g. `master_quiz_doc_parichay.csv`).

---

## Future improvements

- **Automate analytics:** Run the metrics pipeline automatically (e.g. via GitHub Actions) after the last quiz: trigger the poll scraper and analytics, then save the report and CSVs (e.g. into a dated folder like `YYYY results/`) so metrics are gathered without manual steps.
- **Auto-close channels:** Add a way to automatically close or archive the exam channels on the **first Sunday in March** each year (e.g. a scheduled workflow or script that uses the Telegram API to close/restrict the channels).
