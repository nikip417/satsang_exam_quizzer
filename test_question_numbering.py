"""Test to show how questions are numbered for each quiz."""

from datetime import datetime, timedelta


def show_question_numbering(questions_per_quiz=7):
    """
    Show how questions are numbered for each quiz.
    
    The numbering formula is: question_number = (quiz_num - 1) * questions_per_quiz + idx + 1
    where idx is the 0-based index within the quiz.
    This gives sequential numbering across all quizzes.
    """
    print(f"\n{'='*80}")
    print(f"Question Numbering Pattern (assuming {questions_per_quiz} questions per quiz)")
    print(f"{'='*80}\n")
    
    print(f"{'Quiz #':<8} {'Question Index':<18} {'Question Number':<18} {'Example'}")
    print("-" * 80)
    
    total_questions = 0
    
    for quiz_num in range(1, 15):
        for idx in range(questions_per_quiz):
            question_number = ((quiz_num - 1) * questions_per_quiz) + idx + 1
            example = f"Quiz {quiz_num}, Q{idx+1} → #{question_number}"
            
            if idx == 0:
                print(f"{quiz_num:<8} {idx:<18} {question_number:<18} {example}")
            else:
                print(f"{'':<8} {idx:<18} {question_number:<18} {example}")
            
            total_questions = question_number
        
        if quiz_num < 14:
            print("-" * 80)
    
    print(f"\n{'='*80}")
    print(f"Summary:")
    print(f"  - Total quizzes: 14")
    print(f"  - Questions per quiz: {questions_per_quiz}")
    print(f"  - Total questions: {14 * questions_per_quiz}")
    print(f"  - Question numbering range: 1 to {total_questions}")
    print(f"  - Note: Questions are numbered sequentially across all quizzes")
    print(f"{'='*80}\n")
    
    # Show specific examples
    print("Examples:")
    print(f"  Quiz 1, Question 1: (1-1)*7 + 0 + 1 = 1")
    print(f"  Quiz 1, Question 7: (1-1)*7 + 6 + 1 = 7")
    print(f"  Quiz 2, Question 1: (2-1)*7 + 0 + 1 = 8")
    print(f"  Quiz 2, Question 7: (2-1)*7 + 6 + 1 = 14")
    print(f"  Quiz 14, Question 7: (14-1)*7 + 6 + 1 = 98")
    print()
    
    # Show the pattern more clearly
    print("Question Number Pattern by Quiz (Sequential Numbering):")
    print("-" * 80)
    for quiz_num in range(1, 8):  # Show first 7 quizzes
        question_numbers = [((quiz_num - 1) * questions_per_quiz) + idx + 1 
                           for idx in range(questions_per_quiz)]
        print(f"Quiz {quiz_num:2d}: Questions {question_numbers[0]:2d}-{question_numbers[-1]:2d} "
              f"({', '.join(map(str, question_numbers))})")
    print("  ...")
    question_numbers = [((14 - 1) * questions_per_quiz) + idx + 1 
                       for idx in range(questions_per_quiz)]
    print(f"Quiz 14: Questions {question_numbers[0]:2d}-{question_numbers[-1]:2d} "
          f"({', '.join(map(str, question_numbers))})")
    print()


if __name__ == "__main__":
    show_question_numbering(questions_per_quiz=7)

