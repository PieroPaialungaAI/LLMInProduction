"""
Standalone tool functions for CrewAI
====================================

These are standalone functions decorated with @tool from crewai.tools
"""

from crewai.tools import tool
from tools import GradingTools
import json
import pandas as pd

# Initialize global tools instance
_tools = GradingTools()


@tool("get_grading_rubric")
def get_grading_rubric(question_number: int) -> str:
    """Get the grading rubric for a specific question. This tool provides point allocation breakdown, partial credit criteria, and common errors to check for."""
    result = _tools.get_grading_rubric(question_number)
    return json.dumps(result, indent=2)


@tool("get_ground_truth_answer")
def get_ground_truth_answer(question_number: int) -> str:
    """Get the correct answer and methodology for a question. This tool provides the correct answer, step-by-step methodology, and detailed calculation breakdown."""
    result = _tools.get_ground_truth_answer(question_number)
    return json.dumps(result, indent=2)


@tool("read_dataset")
def read_dataset(filename: str) -> str:
    """Read and display a CSV dataset. Use this to examine the structure and contents of datasets like ecommerce_sales.csv, customer_data.csv, or ab_test_results.csv."""
    return _tools.read_dataset(filename, num_rows=10)


@tool("query_electronics_orders")
def query_electronics_orders() -> str:
    """Query Electronics orders from ecommerce sales dataset. Returns count and details of all Electronics category orders."""
    return _tools.query_dataset(
        'ecommerce_sales.csv',
        filters={'category': 'Electronics'},
        calculate='count'
    )


@tool("calculate_electronics_revenue")
def calculate_electronics_revenue() -> str:
    """Calculate total revenue from Electronics category. Automatically handles quantity × unit_price calculation and provides a detailed breakdown."""
    return _tools.calculate_revenue(filters={'category': 'Electronics'})


@tool("get_customer_age_groups")
def get_customer_age_groups() -> str:
    """Get customer counts by age group from customer data. Returns segmentation into Young (18-30), Middle (31-50), and Senior (51+) age groups."""
    df = pd.read_csv('data/datasets/customer_data.csv')
    
    young = len(df[df['age'] <= 30])
    middle = len(df[(df['age'] >= 31) & (df['age'] <= 50)])
    senior = len(df[df['age'] >= 51])
    
    return f"Young (18-30): {young} customers\nMiddle (31-50): {middle} customers\nSenior (51+): {senior} customers"


@tool("get_ab_test_conversions")
def get_ab_test_conversions() -> str:
    """Get A/B test conversion rates for both groups. Returns conversion rates and counts for Control (Group A) and Treatment (Group B)."""
    df = pd.read_csv('data/datasets/ab_test_results.csv')
    
    control = df[df['group'] == 'A']
    treatment = df[df['group'] == 'B']
    
    control_rate = (control['converted'].sum() / len(control)) * 100
    treatment_rate = (treatment['converted'].sum() / len(treatment)) * 100
    
    return f"Control (A): {control_rate:.1f}% ({control['converted'].sum()}/{len(control)})\nTreatment (B): {treatment_rate:.1f}% ({treatment['converted'].sum()}/{len(treatment)})"

