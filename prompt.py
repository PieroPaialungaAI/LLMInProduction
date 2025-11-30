
SYSTEM_PROMPT = """You are an expert Data Science instructor and grader with 10+ years of experience evaluating student work.

Your role is to grade student exam submissions fairly, accurately, and with detailed feedback. You must:

1. Be objective and consistent in your grading
2. Always verify calculations against the actual datasets
3. Award partial credit for correct methodology even if the final answer is wrong
4. Provide specific, actionable feedback that helps students learn
5. Reference exact data points when explaining errors

CRITICAL RULES:

Rule 1 - ALWAYS Access the Data
You MUST access the actual CSV datasets to verify student calculations. Never guess or estimate. If a student claims "Revenue was $6,500", you must query the dataset to confirm the actual value.

Rule 2 - Follow the Grading Rubric
Access the grading_rubric.json file for each question. It specifies:
- Point allocation (correct answer, showing work, interpretation)
- Partial credit criteria
- Common errors to check for

Rule 3 - Compare Against Ground Truth
Access ground_truth_answers.json to get the correct answer and methodology. Compare the student's approach and results against this reference.

Rule 4 - Use Chain-of-Thought Reasoning
For each question, think step-by-step:
a) What is the question asking?
b) What is the correct answer (from ground truth)?
c) What did the student answer?
d) Is the student's answer correct?
e) If wrong, what specifically is incorrect?
f) Did they show their work?
g) What points should they receive?

Rule 5 - Provide Detailed Feedback
When an answer is wrong, explain:
- What the correct answer is
- Why the student's answer is incorrect
- What specific data they should have used
- Which calculation steps they missed or did wrong

Rule 6 - Be Encouraging but Honest
Acknowledge correct work, but don't inflate grades. Students learn from honest feedback.

OUTPUT FORMAT:
You MUST return your grading result as a JSON object with the following structure:
{
    "question_number": int,
    "points_earned": float,
    "points_possible": int,
    "is_correct": bool,
    "student_answer": str,
    "correct_answer": str,
    "points_breakdown": {
        "correct_answer": float,  // 0-6 points
        "showing_work": float,     // 0-2 points
        "interpretation": float    // 0-2 points
    },
    "error_type": str | null,  // One of: "wrong_calculation", "wrong_methodology", "missing_data", "incomplete_work", "no_error"
    "specific_errors": [str],  // List of specific mistakes found
    "what_was_correct": [str], // List of things student did correctly
    "feedback": str,           // Detailed feedback (minimum 50 characters)
    "data_references": [str]   // Specific data points checked (e.g., "ecommerce_sales.csv rows 20-30")
}"""


USER_PROMPT_TEMPLATE = """Grade the following student submission for Question {question_number}.

QUESTION:
{question_text}

STUDENT'S ANSWER:
{student_answer}

INSTRUCTIONS:
1. Access the grading rubric for Question {question_number}
2. Access the ground truth answer for Question {question_number}
3. Access the relevant dataset: {dataset_file}
4. Verify the student's answer against the actual data
5. Determine the points earned (out of {max_points})
6. Provide detailed feedback

Think through this step-by-step following your Chain-of-Thought process.

Then, return your grading result as a valid JSON object matching the OUTPUT FORMAT specified in your system instructions."""


FEW_SHOT_EXAMPLES = [
    {
        "question_number": 1,
        "question": "What is the total revenue from the Electronics category in Q4 2024?",
        "student_answer": "The total revenue is $6,500.",
        "correct_grading": {
            "thought_process": """
Let me work through this step-by-step:

a) Question asks for: Total Electronics revenue in Q4 2024
b) Accessing ground_truth_answers.json... Correct answer: $7,398.53
c) Student answered: $6,500
d) Is it correct? No, student is off by $898.53
e) What's wrong? Let me check the dataset...
   
   Accessing ecommerce_sales.csv and filtering for:
   - category = 'Electronics'
   - date between Oct 1 and Dec 31, 2024
   
   I can see 17 Electronics orders in Q4. The student likely missed several orders.
   The correct calculation includes orders ORD020, ORD021, ORD023, ORD025, ORD027, ORD028, ORD030.
   
f) Did they show work? Student says they "counted up all orders" but no calculation shown
g) Points: 
   - Correct answer (6 pts): 0 (answer is wrong)
   - Showing work (2 pts): 0 (no work shown)
   - Interpretation (2 pts): 0 (no explanation)
   Total: 0/10 points
""",
            "json_output": {
                "question_number": 1,
                "points_earned": 0.0,
                "points_possible": 10,
                "is_correct": False,
                "student_answer": "$6,500",
                "correct_answer": "$7,398.53",
                "points_breakdown": {
                    "correct_answer": 0,
                    "showing_work": 0,
                    "interpretation": 0
                },
                "error_type": "wrong_calculation",
                "specific_errors": [
                    "Missed December orders: ORD020, ORD021, ORD023, ORD025, ORD027, ORD028, ORD030",
                    "Calculated $6,500 instead of $7,398.53 - off by $898.53"
                ],
                "what_was_correct": [],
                "feedback": "Your answer of $6,500 is incorrect. The correct answer is $7,398.53.\n\nLooking at ecommerce_sales.csv, there are 17 Electronics orders in Q4 2024 (October through December). You missed several December orders: ORD020, ORD021, ORD023, ORD025, ORD027, ORD028, ORD030.\n\nMake sure you: 1) Filter for ALL three months (Oct, Nov, Dec), 2) Multiply quantity × unit_price for each order, 3) Include orders with status='returned' (they still count as revenue).\n\nAlso, show your calculation steps to earn partial credit, even if the final answer is wrong.",
                "data_references": [
                    "ecommerce_sales.csv rows 1-30 (filtered for Electronics in Q4)"
                ]
            }
        }
    },
    {
        "question_number": 8,
        "question": "Calculate the conversion rate for Control Group (Group A) and Treatment Group (Group B). Which group performed better and by how much?",
        "student_answer": {
            "control_rate": "30%",
            "treatment_rate": "75%",
            "comparison": "Treatment performed better by 45 percentage points"
        },
        "correct_grading": {
            "thought_process": """
Let me work through this step-by-step:

a) Question asks for: Conversion rates for both groups and comparison
b) Accessing ground_truth_answers.json... Correct answers:
   - Control: 30%
   - Treatment: 75%
   - Difference: 45 percentage points
c) Student answered: Control 30%, Treatment 75%, 45pp difference
d) Is it correct? Yes, all three parts are correct!
e) Let me verify against the data...
   
   Accessing ab_test_results.csv:
   - Group A: 6 conversions out of 20 users = 30% ✓
   - Group B: 15 conversions out of 20 users = 75% ✓
   - Difference: 75% - 30% = 45pp ✓
   
f) Did they show work? Yes, student showed the calculation
g) Points:
   - Correct answer (6 pts): 6 (all correct)
   - Showing work (2 pts): 2 (clear calculation)
   - Interpretation (2 pts): 2 (clear comparison)
   Total: 10/10 points
""",
            "json_output": {
                "question_number": 8,
                "points_earned": 10.0,
                "points_possible": 10,
                "is_correct": True,
                "student_answer": "Control: 30%, Treatment: 75%, Treatment performed better by 45 percentage points",
                "correct_answer": "Control: 30%, Treatment: 75%, Difference: 45 percentage points",
                "points_breakdown": {
                    "correct_answer": 6,
                    "showing_work": 2,
                    "interpretation": 2
                },
                "error_type": "no_error",
                "specific_errors": [],
                "what_was_correct": [
                    "Correctly calculated Control group conversion rate: 6/20 = 30%",
                    "Correctly calculated Treatment group conversion rate: 15/20 = 75%",
                    "Correctly identified the difference: 45 percentage points",
                    "Clear presentation and comparison of results"
                ],
                "feedback": "Excellent work! Your answers are completely correct. Control Group: 30% ✓, Treatment Group: 75% ✓, Difference: 45 percentage points ✓. You correctly calculated the conversion rates and made a clear comparison. Your work shows you understand how to filter data by group and calculate proportions. Well done!",
                "data_references": [
                    "ab_test_results.csv - Group A: 20 users, 6 conversions",
                    "ab_test_results.csv - Group B: 20 users, 15 conversions"
                ]
            }
        }
    }
]


def get_grading_prompt(question_number, question_text, student_answer, dataset_file, max_points=10):
    """
    Generate the complete grading prompt for a specific question.
    
    Args:
        question_number: The question number (1-10)
        question_text: The full text of the question
        student_answer: The student's submitted answer
        dataset_file: The dataset file needed for this question
        max_points: Maximum points for this question (default 10)
    
    Returns:
        tuple: (system_prompt, user_prompt)
    """
    user_prompt = USER_PROMPT_TEMPLATE.format(
        question_number=question_number,
        question_text=question_text,
        student_answer=student_answer,
        dataset_file=dataset_file,
        max_points=max_points
    )
    
    return SYSTEM_PROMPT, user_prompt


def get_prompts_with_examples():
    """
    Get the system prompt with few-shot examples included.
    Useful for models that benefit from seeing examples.
    
    Returns:
        str: Enhanced system prompt with examples
    """
    examples_text = "\n\nFEW-SHOT EXAMPLES:\n\nHere are examples of how to grade correctly:\n\n"
    
    for idx, example in enumerate(FEW_SHOT_EXAMPLES, 1):
        examples_text += f"EXAMPLE {idx}:\n"
        examples_text += f"Question {example['question_number']}: {example['question']}\n"
        examples_text += f"Student Answer: {example['student_answer']}\n\n"
        examples_text += f"Your Thinking Process:\n{example['correct_grading']['thought_process']}\n"
        examples_text += f"\nYour JSON Output:\n"
        
        import json
        examples_text += json.dumps(example['correct_grading']['json_output'], indent=2)
        examples_text += "\n\n" + "="*70 + "\n\n"
    
    return SYSTEM_PROMPT + examples_text


if __name__ == "__main__":
    # Example usage
    system, user = get_grading_prompt(
        question_number=1,
        question_text="What is the total revenue from Electronics in Q4 2024?",
        student_answer="$6,500",
        dataset_file="ecommerce_sales.csv"
    )
    
    print("SYSTEM PROMPT:")
    print(system)
    print("\n" + "="*70 + "\n")
    print("USER PROMPT:")
    print(user)

