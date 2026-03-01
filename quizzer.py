import asyncio
from datetime import datetime, timedelta

import pandas as pd
from telegram import Bot  # type: ignore
from telegram.error import NetworkError, TimedOut  # type: ignore

# Telegram API configuration
bot_token = '7729813240:AAF4Szlc-zZv-8_iWbtibJqsrCVMv4E7pds'
telegram_chat_info = {
    'prarambh': -1003321762542,
    'parichay': -1003404539281,
    'pravesh': -1003343356200,
    'pravin': -1003238390901
}

# Exam types
exams = ['prarambh', 'parichay', 'pravesh', 'pravin']

def get_quiz_number():
    """
    Calculate quiz number based on Monday/Thursday schedule starting first week of January.
    Returns the quiz number for the current or next quiz, or None if:
    - Before the first quiz of the year, or
    - Quiz number is greater than 14
    """
    today = datetime.now()
    current_year = today.year
    
    # Find first Monday of January
    jan_1 = datetime(current_year, 1, 1)
    days_until_monday = (7 - jan_1.weekday()) % 7
    if days_until_monday == 0 and jan_1.weekday() != 0:
        days_until_monday = 7
    first_monday = jan_1 + timedelta(days=days_until_monday)
    
    # Calculate days since first Monday
    days_since_start = (today - first_monday).days
    if days_since_start < 0:
        print(f'Before first quiz of the year...')
        return None  # Before first quiz of the year
    
    # Calculate which week we're in (0-indexed)
    week_number = days_since_start // 7
    
    # Calculate day of week (0=Monday, 3=Thursday)
    day_of_week = today.weekday()
    
    # Determine quiz number
    if day_of_week == 0:  # Monday
        quiz_no = (week_number * 2) + 1
    elif day_of_week < 3:  # Tuesday or Wednesday
        quiz_no = (week_number * 2) + 1  # Next quiz is Monday (this week)
    elif day_of_week == 3:  # Thursday
        quiz_no = (week_number * 2) + 2
    else:  # Friday, Saturday, Sunday
        quiz_no = ((week_number + 1) * 2) + 1  # Next quiz is next Monday
    
    # Don't send quizzes beyond quiz 14
    if quiz_no > 14:
        print(f'Quiz number {quiz_no} is past number of available quizzes...')
        return None
    
    return quiz_no


def load_quiz_data(quiz_no):
    """Load quiz data from CSV file, filtering by quiz_no for each exam."""
    quiz_data = {}
    print(f'Loading quiz data for quiz number {quiz_no}...')
    for exam_name in exams:
        # Read the CSV file
        df = pd.read_csv(f'quiz_data/master_quiz_doc_{exam_name}.csv')
        
        # Filter rows where quiz_number column matches quiz_no
        filtered_df = df[df['quiz_num'] == quiz_no]
        
        quiz_data[exam_name] = filtered_df
        print(f'Loaded {exam_name} quiz data: {len(filtered_df)} rows with quiz_no={quiz_no}')
    
    return quiz_data

async def post_quiz(exam_name, quiz_info):
    """Post a quiz to Telegram with retry logic."""
    chat_id = telegram_chat_info[exam_name]
    bot = Bot(token=bot_token)
    
    question = quiz_info['question']
    options = quiz_info['options']
    correct_option_id = quiz_info['answer_index']
    explanation = quiz_info['explanation']

    max_retries = 5
    for attempt in range(max_retries):
        try:
            await bot.send_poll(
                chat_id=chat_id,
                question=question,
                options=options,
                type='quiz',
                is_anonymous=True,
                correct_option_id=correct_option_id,
                explanation=explanation,
                protect_content=True
            )
            return
        except (TimedOut, NetworkError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Attempt {attempt + 1} failed: {type(e).__name__}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                print(f"Failed after {max_retries} attempts: {type(e).__name__}")
                raise

async def process_exam_quizzes(exam_name, df):
    """Process and post quizzes for a single exam sequentially."""
    print(f"\n--- Processing {exam_name.upper()} ({len(df)} rows) ---")
    
    # Sort by quiz_num to ensure order, then reset index for sequential numbering
    df_sorted = df.sort_values('quiz_num').reset_index(drop=True)
    
    for idx, (_, row) in enumerate(df_sorted.iterrows()):
        # Build options list, filtering out NaN and empty values
        original_answer_index = int(row['answer index'])
        options = []
        valid_indices = []
        
        for i in range(4):
            if pd.notna(row[f'option{i}']) and row[f'option{i}']:
                options.append(row[f'option{i}'])
                valid_indices.append(i)
        
        # Adjust answer_index: find position of correct answer in filtered list
        if original_answer_index in valid_indices:
            answer_index = valid_indices.index(original_answer_index)
        else:
            print(f"Warning: Correct answer index {original_answer_index} not found in valid options "
                  f"for quiz {row['quiz_num']} in {exam_name}")
            continue
        
        # Build quiz_info dictionary from row data
        # Sequential numbering: Quiz 1 = 1-7, Quiz 2 = 8-14, Quiz 3 = 15-21, etc.
        question_number = ((row["quiz_num"] - 1) * 7) + idx + 1
        quiz_info = {
            'question': f'{question_number}. {row["question"]}',
            'options': options,
            'answer_index': answer_index,
            'explanation': f'{row["Book Name"]} - Chapter {row["chapter_no"]}: {row["Chapter Name"]} - Page {row["page_no"]}'
        }
        
        try:
            await post_quiz(exam_name, quiz_info)
            print(f"Posted quiz {row['quiz_num'] + idx} for {exam_name}")
        except Exception as e:
            print(f"Failed to post quiz {row['quiz_num'] + idx} for {exam_name}: {type(e).__name__}: {e}")
            continue

async def process_and_post_quizzes(quiz_data):
    """Process quiz data and post each quiz question.
    
    Exams run in parallel, but questions within each exam are posted sequentially.
    """
    tasks = [process_exam_quizzes(exam_name, quiz_data[exam_name]) for exam_name in exams]
    await asyncio.gather(*tasks)