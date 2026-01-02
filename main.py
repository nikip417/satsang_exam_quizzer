import asyncio

from quizzer import get_quiz_number, load_quiz_data, process_and_post_quizzes


def main():
    """Main entry point for the quiz posting application."""
    quiz_no = get_quiz_number()
    
    if quiz_no is None:
        print("No quiz scheduled - either before the first quiz of the year or beyond the last quiz of the year.")
        return
    
    print(f'Loading quiz data for quiz number {quiz_no}...')
    quiz_data = load_quiz_data(quiz_no)
    asyncio.run(process_and_post_quizzes(quiz_data))


if __name__ == "__main__":
    main()
