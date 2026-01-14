"""Test cases to visualize quiz numbering for all 14 quiz days."""

from datetime import datetime, timedelta

from quizzer import get_quiz_number


def get_quiz_number_for_date(test_date):
    """Calculate quiz number for a specific date (for testing)."""
    current_year = test_date.year
    
    # Find first Monday of January
    jan_1 = datetime(current_year, 1, 1)
    days_until_monday = (7 - jan_1.weekday()) % 7
    if days_until_monday == 0 and jan_1.weekday() != 0:
        days_until_monday = 7
    first_monday = jan_1 + timedelta(days=days_until_monday)
    
    # Calculate days since first Monday
    days_since_start = (test_date - first_monday).days
    if days_since_start < 0:
        return None
    
    # Calculate which week we're in (0-indexed)
    week_number = days_since_start // 7
    
    # Calculate day of week (0=Monday, 3=Thursday)
    day_of_week = test_date.weekday()
    
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
        return None
    
    return quiz_no


def test_all_quiz_days(year=2026):
    """Test and display all 14 quiz days for a given year."""
    print(f"\n{'='*70}")
    print(f"Quiz Numbering Schedule for Year {year}")
    print(f"{'='*70}\n")
    
    # Find first Monday of January
    jan_1 = datetime(year, 1, 1)
    days_until_monday = (7 - jan_1.weekday()) % 7
    if days_until_monday == 0 and jan_1.weekday() != 0:
        days_until_monday = 7
    first_monday = jan_1 + timedelta(days=days_until_monday)
    
    print(f"First Monday of {year}: {first_monday.strftime('%A, %B %d, %Y')}\n")
    print(f"{'Quiz #':<8} {'Date':<20} {'Day':<12} {'Week':<8} {'Status'}")
    print("-" * 70)
    
    # Calculate all 14 quiz dates
    quiz_dates = []
    current_date = first_monday
    
    for quiz_num in range(1, 15):
        if quiz_num % 2 == 1:  # Odd numbers are Mondays
            # Find the Monday for this quiz
            week_num = (quiz_num - 1) // 2
            quiz_date = first_monday + timedelta(weeks=week_num)
            quiz_dates.append((quiz_num, quiz_date, 'Monday'))
        else:  # Even numbers are Thursdays
            # Find the Thursday for this quiz
            week_num = (quiz_num - 2) // 2
            quiz_date = first_monday + timedelta(weeks=week_num, days=3)
            quiz_dates.append((quiz_num, quiz_date, 'Thursday'))
    
    # Display each quiz day
    for quiz_num, quiz_date, day_name in quiz_dates:
        calculated_quiz = get_quiz_number_for_date(quiz_date)
        status = "✓" if calculated_quiz == quiz_num else f"✗ (got {calculated_quiz})"
        week_num = (quiz_date - first_monday).days // 7
        print(f"{quiz_num:<8} {quiz_date.strftime('%Y-%m-%d'):<20} {day_name:<12} {week_num:<8} {status}")
    
    # Test edge cases
    print(f"\n{'='*70}")
    print("Edge Case Tests")
    print(f"{'='*70}\n")
    
    # Before first quiz
    before_first = first_monday - timedelta(days=1)
    result = get_quiz_number_for_date(before_first)
    print(f"Before first quiz ({before_first.strftime('%Y-%m-%d')}): {result} (should be None)")
    
    # Day before each quiz (should show next quiz)
    print(f"\nDays before quizzes (should show next quiz number):")
    for quiz_num, quiz_date, day_name in quiz_dates[:5]:  # Show first 5
        day_before = quiz_date - timedelta(days=1)
        result = get_quiz_number_for_date(day_before)
        print(f"  {day_before.strftime('%Y-%m-%d')} (day before quiz {quiz_num}): {result}")
    
    # After quiz 14
    last_quiz_date = quiz_dates[-1][1]
    after_last = last_quiz_date + timedelta(days=7)
    result = get_quiz_number_for_date(after_last)
    print(f"\nAfter quiz 14 ({after_last.strftime('%Y-%m-%d')}): {result} (should be None)")
    
    # Test different days of the week for a specific week
    print(f"\n{'='*70}")
    print("Example: Week 2 (Mon-Wed: quiz 5, Thu: quiz 6, Fri-Sun: quiz 7)")
    print(f"{'='*70}\n")
    week_2_monday = first_monday + timedelta(weeks=2)
    for days_offset in range(7):
        test_date = week_2_monday + timedelta(days=days_offset)
        result = get_quiz_number_for_date(test_date)
        day_name = test_date.strftime('%A')
        print(f"  {test_date.strftime('%Y-%m-%d')} ({day_name:<9}): Quiz {result}")


if __name__ == "__main__":
    # Test for 2026
    test_all_quiz_days(2026)
    
    # Test for 2025 (different first Monday)
    print("\n\n")
    test_all_quiz_days(2025)

