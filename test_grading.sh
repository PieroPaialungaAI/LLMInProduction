#!/bin/bash

# Quick test script for grading system
# Make sure OPENAI_API_KEY is set before running

echo "Testing LLM Grading System"
echo "=========================="
echo ""
echo "Option 1: Grade just 2 questions from full submission"
echo "python main.py --submission ../data/sample_student_submission.json --limit 2"
echo ""
echo "Option 2: Grade short submission (only 2 questions)"
echo "python main.py --submission ../data/sample_student_submission_short.json"
echo ""
echo "Option 3: Grade 1 question only"
echo "python main.py --submission ../data/sample_student_submission.json --limit 1"
echo ""
echo "Run one of these commands to test!"
