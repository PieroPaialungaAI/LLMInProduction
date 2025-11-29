# LLM-Based Student Grading System

## Overview
This system demonstrates how to use LLMs with tools/RAG to grade student assignments. The LLM **cannot** answer the questions without accessing the tools because the questions require specific data analysis of course-provided datasets.

## System Architecture

### 1. Student-Facing Materials
- `data/test.json` - The exam questions students must answer (structured JSON format)
- `data/datasets/` - Three CSV files students must analyze:
  - `ecommerce_sales.csv` - Sales transaction data (30 transactions)
  - `customer_data.csv` - Customer demographics and spending (16 customers)
  - `ab_test_results.csv` - A/B test experiment data (40 users)

### 2. Grading Tools (LLM must access these)
- `data/class_resources/grading_rubric.json` - Detailed grading criteria for each question
- `data/class_resources/ground_truth_answers.json` - Correct answers with full solutions
- `data/datasets/*.csv` - The actual data to verify student calculations

### 3. Student Submissions
- `data/sample_student_submission.json` - Example submission with some incorrect answers for testing

### 3. Why LLM Needs Tools

**The LLM CANNOT grade without accessing tools because:**
1. Questions ask about specific datasets ("ecommerce_sales.csv from Week 5")
2. The LLM doesn't know what's in these course-specific datasets
3. To verify student answers, the LLM must:
   - Read `grading_rubric.json` to understand how to grade
   - Read `ground_truth_answers.json` to get expected answers
   - Read the actual CSV files to verify student calculations
   - Compare student work against the actual data
   - Explain WHY answers are wrong using specific data points

## Example Workflow

**Question:** "What is the total revenue from Electronics in Q4 2024?"

**Student Answer:** "$6,500"

**LLM Grading Process:**
1. Parse `sample_student_submission.json` to read student's answer
2. Access `grading_rubric.json` to see this question is worth 10 points
3. Access `ground_truth_answers.json` to see correct answer is $7,398.53
4. Access `ecommerce_sales.csv` to verify the calculation against actual data
5. Compare student's $6,500 vs correct $7,398.53
6. Provide feedback: "Incorrect. You got $6,500 but the correct answer is $7,398.53. Looking at ecommerce_sales.csv, you may have missed orders ORD020, ORD021, ORD023, ORD025, ORD027, ORD028, and ORD030. Make sure you included ALL Electronics orders from October, November, AND December 2024."

## Files Created

```
data/
├── test.json (exam questions - structured format)
├── sample_student_submission.json (example submission to grade)
├── class_resources/
│   ├── grading_rubric.json (grading criteria - TOOL)
│   └── ground_truth_answers.json (correct answers with detailed solutions - TOOL)
└── datasets/
    ├── ecommerce_sales.csv (30 sales transactions - TOOL)
    ├── customer_data.csv (16 customer records - TOOL)
    └── ab_test_results.csv (40 user A/B test results - TOOL)
```

## Data Format Decisions

- **CSV for datasets**: Raw data that students analyze (realistic format)
- **JSON for everything else**: Structured format that's easy for LLMs to parse
  - Test questions with metadata
  - Grading rubrics with hierarchical criteria
  - Ground truth answers with detailed breakdowns
  - Student submissions with structured responses

## Next Steps

To implement the LLM grading system:
1. Define tools for the LLM to access class_resources and datasets
2. Create a grading prompt that instructs the LLM to:
   - Read the student submission
   - Access grading rubric for criteria
   - Access ground truth answers for expected results
   - Access actual datasets to verify calculations
   - Provide detailed feedback with specific data references
3. Implement guardrails to ensure the LLM:
   - Always checks the actual data
   - Provides specific examples from the data when explaining errors
   - Awards partial credit per the rubric
4. Add structured output for consistent grade reporting

## Key Design Principle

The questions are **dataset-specific**, not general knowledge questions. The LLM must query the actual data to grade accurately. This ensures the LLM truly needs RAG/tools rather than just using its training data.

