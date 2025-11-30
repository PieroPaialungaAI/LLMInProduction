"""
CrewAI Tasks Configuration for LLM Grading System
==================================================

Defines grading tasks and their expected outputs.
"""

from crewai import Task
from schemas import GradingResult
from prompt import USER_PROMPT_TEMPLATE


def create_grading_task(
    agent,
    question_number: int,
    question_text: str,
    student_answer: str,
    dataset_file: str,
    max_points: int = 10
) -> Task:
    """
    Create a grading task for a specific question.
    
    Args:
        agent: The grader agent
        question_number: Question number (1-10)
        question_text: Full text of the question
        student_answer: Student's submitted answer
        dataset_file: Dataset file needed for this question
        max_points: Maximum points for the question
        
    Returns:
        Configured CrewAI Task
    """
    
    # Generate the prompt
    description = USER_PROMPT_TEMPLATE.format(
        question_number=question_number,
        question_text=question_text,
        student_answer=student_answer,
        dataset_file=dataset_file,
        max_points=max_points
    )
    
    # Define expected output structure
    student_answer_preview = student_answer[:50] if len(student_answer) > 50 else student_answer
    expected_output = f"""A complete grading result in JSON format with these exact fields:
{{
    "question_number": {question_number},
    "points_earned": <float between 0 and {max_points}>,
    "points_possible": {max_points},
    "is_correct": <boolean>,
    "student_answer": "{student_answer_preview}...",
    "correct_answer": "<the verified correct answer from ground truth>",
    "points_breakdown": {{
        "correct_answer": <0-6 points>,
        "showing_work": <0-2 points>,
        "interpretation": <0-2 points>
    }},
    "error_type": "<one of: wrong_calculation, wrong_methodology, missing_data, incomplete_work, no_error>",
    "specific_errors": ["<list of specific mistakes>"],
    "what_was_correct": ["<list of correct elements>"],
    "feedback": "<detailed feedback with at least 50 characters explaining the grade>",
    "data_references": ["<specific data points checked, e.g., 'ecommerce_sales.csv rows 1-30'>"]
}}

The JSON must be valid and match the GradingResult Pydantic schema exactly.
"""
    
    task = Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_json=GradingResult  # Enforce structured output
    )
    
    return task


def create_validation_task(
    agent,
    grading_result: dict,
    question_number: int
) -> Task:
    """
    Create a validation task to review a grading result.
    
    Args:
        agent: The validation agent
        grading_result: The grading result to validate
        question_number: Question number being validated
        
    Returns:
        Configured CrewAI Task
    """
    
    description = f"""Review the following grading result for Question {question_number} and check for:

1. **Consistency**: Do the points_earned match the points_breakdown sum?
2. **Logic**: If marked incorrect, are specific_errors provided?
3. **Policy Compliance**: 
   - Wrong answers must have detailed feedback (min 50 chars)
   - Data-related errors must include data_references
   - Zero points requires at least 2 specific errors
4. **Feedback Quality**: Is the feedback constructive and specific?
5. **Fairness**: Is partial credit awarded appropriately?

Grading Result to Review:
{grading_result}

Provide your validation report in JSON format:
{{
    "is_valid": <boolean>,
    "consistency_issues": ["<list of issues>"],
    "policy_violations": ["<list of violations>"],
    "feedback_quality_score": <1-10>,
    "recommendations": ["<improvements if any>"],
    "overall_assessment": "<summary>"
}}
"""
    
    expected_output = """A validation report in JSON format assessing the grading result's 
    quality, consistency, and policy compliance."""
    
    task = Task(
        description=description,
        expected_output=expected_output,
        agent=agent
    )
    
    return task


def create_batch_grading_tasks(
    agent,
    submissions: list
) -> list:
    """
    Create multiple grading tasks for batch processing.
    
    Args:
        agent: The grader agent
        submissions: List of submission dicts with question_number, question_text, 
                    student_answer, dataset_file
        
    Returns:
        List of CrewAI Tasks
    """
    
    tasks = []
    
    for submission in submissions:
        task = create_grading_task(
            agent=agent,
            question_number=submission['question_number'],
            question_text=submission['question_text'],
            student_answer=submission['student_answer'],
            dataset_file=submission['dataset_file'],
            max_points=submission.get('max_points', 10)
        )
        tasks.append(task)
    
    return tasks


if __name__ == "__main__":
    # Test task creation
    from agents import create_grader_agent
    
    print("Creating test grading task...")
    agent = create_grader_agent()
    
    task = create_grading_task(
        agent=agent,
        question_number=1,
        question_text="What is the total revenue from Electronics in Q4 2024?",
        student_answer="$6,500",
        dataset_file="ecommerce_sales.csv"
    )
    
    print(f"✅ Task created")
    print(f"   Description length: {len(task.description)} chars")
    print(f"   Expected output defined: Yes")
    print(f"   Output schema: {task.output_json}")

