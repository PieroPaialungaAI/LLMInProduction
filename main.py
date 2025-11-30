"""
Main Entry Point for LLM Grading System
========================================

Command-line interface for grading student submissions.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from crew import GradingCrew
from schemas import GradingResult

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use system env vars


def load_test_questions(test_file: str = "data/test.json") -> dict:
    """Load test questions from JSON file."""
    with open(test_file, 'r') as f:
        return json.load(f)


def load_student_submission(submission_file: str) -> dict:
    """Load student submission from JSON file."""
    with open(submission_file, 'r') as f:
        return json.load(f)


def map_question_to_dataset(question_number: int, test_data: dict) -> str:
    """Map question number to its dataset file."""
    for section in test_data['sections']:
        for question in section['questions']:
            if question['question_number'] == question_number:
                return section['dataset']
    return "unknown.csv"


def grade_submission(
    submission_file: str,
    model: str = "gpt-4",
    temperature: float = 0.1,
    output_file: str = None,
    verbose: bool = True,
    student_id: str = None,
    limit: int = None
):
    """
    Grade a student submission.
    
    Args:
        submission_file: Path to student submission JSON
        model: LLM model to use
        temperature: Temperature for generation
        output_file: Optional output file for results
        verbose: Whether to print detailed logs
        student_id: Optional student ID
        limit: Optional limit on number of questions to grade
    """
    
    print("="*70)
    print("LLM Grading System - Production Mode")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Model: {model}")
    print(f"  Temperature: {temperature}")
    print(f"  Submission: {submission_file}")
    print(f"  Output: {output_file or 'stdout'}")
    print()
    
    # Load data
    print("Loading data...")
    try:
        test_data = load_test_questions()
        submission_data = load_student_submission(submission_file)
        print(f"✅ Test questions loaded: {len(test_data['sections'])} sections")
        print(f"✅ Student submission loaded")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        sys.exit(1)
    
    # Extract student info
    student_name = submission_data.get('student_name', 'Unknown Student')
    exam_date = submission_data.get('exam_date', datetime.now().strftime('%Y-%m-%d'))
    answers = submission_data.get('answers', [])
    
    print(f"\nStudent: {student_name}")
    print(f"Exam Date: {exam_date}")
    print(f"Questions to Grade: {len(answers)}")
    if limit and limit < len(answers):
        print(f"⚠️  Limiting to first {limit} question(s)")
    print()
    
    # Initialize crew
    print("Initializing grading crew...")
    crew_manager = GradingCrew(
        model_name=model,
        temperature=temperature,
        verbose=verbose
    )
    print("✅ Crew initialized\n")
    
    # Prepare submissions
    submissions = []
    for answer in answers:
        question_number = answer['question_number']
        dataset_file = map_question_to_dataset(question_number, test_data)
        
        # Find full question text
        question_text = ""
        for section in test_data['sections']:
            for q in section['questions']:
                if q['question_number'] == question_number:
                    question_text = q['question']
                    break
        
        submissions.append({
            'question_number': question_number,
            'question_text': question_text,
            'student_answer': answer['student_answer'],
            'dataset_file': dataset_file
        })
    
    # Apply limit if specified
    if limit and limit < len(submissions):
        submissions = submissions[:limit]
        print(f"✓ Grading only the first {limit} question(s)\n")
    
    # Grade all questions
    print("Starting grading process...\n")
    results, messages = crew_manager.grade_multiple_questions(
        submissions=submissions,
        student_id=student_id or student_name
    )
    
    # Create exam report
    print("\n" + "="*70)
    print("Creating Exam Report")
    print("="*70 + "\n")
    
    report = crew_manager.create_exam_report(
        results=results,
        student_name=student_name,
        exam_date=exam_date
    )
    
    # Print summary
    print(f"Student: {report['student_name']}")
    print(f"Score: {report['total_points_earned']}/{report['total_points_possible']} ({report['percentage']:.1f}%)")
    print(f"Grade: {report['letter_grade']}")
    print(f"\nStrengths:")
    for strength in report['strengths']:
        print(f"  ✓ {strength}")
    print(f"\nAreas for Improvement:")
    for area in report['areas_for_improvement']:
        print(f"  • {area}")
    print(f"\nOverall Feedback:")
    print(f"  {report['overall_feedback']}")
    
    # Save results
    if output_file:
        print(f"\nSaving results to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print("✅ Results saved")
    
    # Print individual question results
    print("\n" + "="*70)
    print("Individual Question Results")
    print("="*70 + "\n")
    
    for i, result in enumerate(results, 1):
        print(f"Question {result.question_number}: {result.points_earned}/{result.points_possible} points")
        print(f"  Student Answer: {result.student_answer[:80]}...")
        print(f"  Correct Answer: {result.correct_answer[:80]}...")
        print(f"  Status: {'✓ Correct' if result.is_correct else '✗ Incorrect'}")
        print()
    
    print("="*70)
    print("Grading Complete!")
    print("="*70)


def main():
    """Main CLI entry point."""
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found!")
        print("\nPlease set your OpenAI API key using one of these methods:")
        print("\n1. Environment variable (recommended):")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print("\n2. Create a .env file in the project root:")
        print("   OPENAI_API_KEY=your-api-key-here")
        print("\n3. Set it inline:")
        print("   OPENAI_API_KEY='your-key' python main.py --submission ...")
        print()
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="LLM-based automated grading system for Data Science exams",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Grade a submission with default settings
  python main.py --submission data/sample_student_submission.json

  # Grade with specific model and save output
  python main.py --submission data/sample_student_submission.json \\
                 --model gpt-4 \\
                 --output results/jane_doe_grades.json

  # Grade with custom temperature and student ID
  python main.py --submission data/sample_student_submission.json \\
                 --temperature 0.2 \\
                 --student-id jane.doe@university.edu \\
                 --verbose
        """
    )
    
    parser.add_argument(
        '--submission',
        type=str,
        required=True,
        help='Path to student submission JSON file'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4',
        help='LLM model to use (default: gpt-4)'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.1,
        help='Temperature for LLM generation (default: 0.1)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file for grading results (default: stdout only)'
    )
    
    parser.add_argument(
        '--student-id',
        type=str,
        default=None,
        help='Student ID for rate limiting and tracking'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress non-essential output'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of questions to grade (e.g., --limit 2 for first 2 questions)'
    )
    
    args = parser.parse_args()
    
    # Validate submission file exists
    if not Path(args.submission).exists():
        print(f"❌ Error: Submission file not found: {args.submission}")
        sys.exit(1)
    
    # Run grading
    try:
        grade_submission(
            submission_file=args.submission,
            model=args.model,
            temperature=args.temperature,
            output_file=args.output,
            verbose=args.verbose and not args.quiet,
            student_id=args.student_id,
            limit=args.limit
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Grading interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

