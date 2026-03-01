import asyncio
import csv
from pathlib import Path

from telethon import TelegramClient

from quizzer import telegram_chat_info, bot_token

# Replace these with your own values from https://my.telegram.org
API_ID = 32912645  # TODO: set your API ID here
API_HASH = "a508eaaa7489e4631e9c11ce9b2d6d8d"  # TODO: set your API hash here

# Session file will be created in the current directory on first run
SESSION_NAME = "scrape_polls"

HISTORICAL_POLL_LOG_FILE = Path("2026 results/historical_poll_log.csv")


async def scrape_channel_polls(client: TelegramClient, exam_name: str, chat_id: int, writer: csv.DictWriter) -> None:
    """
    Walk through the full message history of a channel and record all poll message IDs.
    """
    entity = await client.get_entity(chat_id)
    print(f"Scraping polls for {exam_name} (chat_id={chat_id})...")

    async for message in client.iter_messages(entity, limit=None):
        if not getattr(message, "poll", None):
            continue

        question_text = (message.message or "").replace("\n", " ")

        total_voters = 0
        try:
            results = getattr(message, "poll", None).results  # type: ignore[assignment]
            print(results)
            if results and getattr(results, "total_voters", None) is not None:
                total_voters = int(results.total_voters)
        except Exception:
            # If result metadata isn't available, just skip the total_voters value
            total_voters = 0

        writer.writerow(
            {
                "exam_name": exam_name,
                "chat_id": chat_id,
                "message_id": message.id,
                "question": question_text,
                "date": message.date.isoformat() if message.date else "",
                "total_voters": total_voters,
            }
        )


async def main() -> None:
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    file_exists = HISTORICAL_POLL_LOG_FILE.exists()
    with HISTORICAL_POLL_LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        fieldnames = ["exam_name", "chat_id", "message_id", "question", "date", "total_voters"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        async with client:
            await client.start()  # On first run, this will ask for your phone and code

            for exam_name, chat_id in telegram_chat_info.items():
                await scrape_channel_polls(client, exam_name, chat_id, writer)

    print(f"\nDone. Historical poll data saved to {HISTORICAL_POLL_LOG_FILE}")


if __name__ == "__main__":
    asyncio.run(main())

