from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from enum import Enum


class QuestionType(str, Enum):
    """Types of questions on the exam"""
    CALCULATION = "calculation"
    ANALYSIS = "analysis"
    INTERPRETATION = "interpretation"
    STATISTICAL = "statistical"


class GradingResult(BaseModel):
    """
    Structured output for a single question's grading result.
    
    This replaces free-form text with a validated structure.
    """
    question_number: int = Field(..., ge=1, le=10, description="Question number (1-10)")
    
    points_earned: float = Field(..., ge=0, le=10, description="Points earned out of 10")
    points_possible: int = Field(default=10, description="Maximum points for this question")
    
    is_correct: bool = Field(..., description="Whether the answer is fully correct")
    
    student_answer: str = Field(..., description="The student's submitted answer")
    correct_answer: str = Field(..., description="The correct answer")
    
    # Breakdown by grading criteria
    points_breakdown: dict = Field(
        ..., 
        description="Points breakdown: correct_answer, showing_work, interpretation"
    )
    
    # Detailed analysis
    error_type: Optional[Literal[
        "wrong_calculation", 
        "wrong_methodology", 
        "missing_data", 
        "incomplete_work",
        "no_error"
    ]] = Field(None, description="Type of error if incorrect")
    
    specific_errors: List[str] = Field(
        default_factory=list,
        description="List of specific errors found (e.g., 'Missed orders ORD020, ORD021')"
    )
    
    what_was_correct: List[str] = Field(
        default_factory=list,
        description="What the student did correctly (for partial credit)"
    )
    
    feedback: str = Field(..., min_length=50, description="Detailed feedback for the student")
    
    data_references: List[str] = Field(
        default_factory=list,
        description="Specific data points referenced (e.g., 'ecommerce_sales.csv rows 5-10')"
    )
    
    @validator('student_answer', pre=True)
    def parse_student_answer(cls, v):
        """Handle case where LLM returns dict instead of string"""
        if isinstance(v, dict):
            # Extract value from dict if present
            return v.get('value', str(v))
        return v
    
    @validator('correct_answer', pre=True)
    def parse_correct_answer(cls, v):
        """Handle case where LLM returns dict instead of string"""
        if isinstance(v, dict):
            # Extract value from dict if present
            return v.get('value', str(v))
        return v
    
    @validator('points_earned')
    def validate_points(cls, v, values):
        """Ensure points don't exceed maximum"""
        if v > values.get('points_possible', 10):
            raise ValueError('Points earned cannot exceed points possible')
        return v
    
    @validator('points_breakdown')
    def validate_breakdown(cls, v, values):
        """Ensure breakdown sums correctly"""
        total = sum(v.values())
        expected = values.get('points_earned', 0)
        if abs(total - expected) > 0.01:  # Allow small floating point differences
            raise ValueError(f'Points breakdown ({total}) must sum to points_earned ({expected})')
        return v
    
    def get_percentage(self) -> float:
        """Calculate percentage score"""
        return (self.points_earned / self.points_possible) * 100
    
    def to_display_format(self) -> str:
        """Format for human-readable display"""
        return f"""
Question {self.question_number}: {self.points_earned}/{self.points_possible} points ({self.get_percentage():.1f}%)

Student Answer: {self.student_answer}
Correct Answer: {self.correct_answer}

Points Breakdown:
  - Correct Answer: {self.points_breakdown.get('correct_answer', 0)}/6
  - Showing Work: {self.points_breakdown.get('showing_work', 0)}/2
  - Interpretation: {self.points_breakdown.get('interpretation', 0)}/2

{self.feedback}
"""


class ExamGradingReport(BaseModel):
    """
    Complete grading report for the entire exam.
    Aggregates all question results.
    """
    student_name: str = Field(..., description="Name of the student")
    exam_date: str = Field(..., description="Date of the exam")
    
    question_results: List[GradingResult] = Field(
        ..., 
        min_items=1,
        description="Grading results for each question"
    )
    
    total_points_earned: float = Field(..., ge=0, description="Total points across all questions")
    total_points_possible: int = Field(..., ge=1, description="Total possible points")
    
    overall_percentage: float = Field(..., ge=0, le=100, description="Overall percentage score")
    
    letter_grade: Literal["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"] = Field(
        ..., description="Letter grade based on percentage"
    )
    
    strengths: List[str] = Field(
        default_factory=list,
        description="Areas where student performed well"
    )
    
    areas_for_improvement: List[str] = Field(
        default_factory=list,
        description="Areas needing more work"
    )
    
    overall_feedback: str = Field(
        ..., 
        min_length=100,
        description="Overall assessment and recommendations"
    )
    
    grading_timestamp: str = Field(..., description="When grading was completed")
    
    @validator('total_points_earned')
    def validate_total_points(cls, v, values):
        """Ensure total matches sum of individual questions"""
        if 'question_results' in values:
            calculated_total = sum(q.points_earned for q in values['question_results'])
            if abs(calculated_total - v) > 0.01:
                raise ValueError(f'Total points ({v}) must match sum of question points ({calculated_total})')
        return v
    
    @validator('letter_grade')
    def validate_letter_grade(cls, v, values):
        """Ensure letter grade matches percentage"""
        pct = values.get('overall_percentage', 0)
        expected = calculate_letter_grade(pct)
        if v != expected:
            raise ValueError(f'Letter grade {v} does not match percentage {pct} (expected {expected})')
        return v
    
    def get_summary_stats(self) -> dict:
        """Get summary statistics"""
        return {
            "total_questions": len(self.question_results),
            "questions_correct": sum(1 for q in self.question_results if q.is_correct),
            "average_points_per_question": self.total_points_earned / len(self.question_results),
            "percentage": self.overall_percentage,
            "grade": self.letter_grade
        }


def calculate_letter_grade(percentage: float) -> str:
    """
    Calculate letter grade from percentage.
    Standard grading scale.
    """
    if percentage >= 93:
        return "A"
    elif percentage >= 90:
        return "A-"
    elif percentage >= 87:
        return "B+"
    elif percentage >= 83:
        return "B"
    elif percentage >= 80:
        return "B-"
    elif percentage >= 77:
        return "C+"
    elif percentage >= 73:
        return "C"
    elif percentage >= 70:
        return "C-"
    elif percentage >= 60:
        return "D"
    else:
        return "F"


# Example usage for type checking and validation
if __name__ == "__main__":
    from datetime import datetime
    
    # Example: Creating a grading result
    result = GradingResult(
        question_number=1,
        points_earned=7.0,
        points_possible=10,
        is_correct=False,
        student_answer="$6,500",
        correct_answer="$7,398.53",
        points_breakdown={
            "correct_answer": 3,  # Partial credit
            "showing_work": 2,
            "interpretation": 2
        },
        error_type="wrong_calculation",
        specific_errors=[
            "Missed December orders: ORD020, ORD021, ORD023",
            "Did not include all Electronics items"
        ],
        what_was_correct=[
            "Correctly identified Q4 date range",
            "Showed calculation methodology"
        ],
        feedback="Your approach was correct, but you missed several orders...",
        data_references=["ecommerce_sales.csv rows 20-30"]
    )
    
    print("✅ Valid GradingResult created:")
    print(result.to_display_format())
    
    # Example: Creating full exam report
    report = ExamGradingReport(
        student_name="Jane Doe",
        exam_date="2024-11-29",
        question_results=[result],
        total_points_earned=7.0,
        total_points_possible=10,
        overall_percentage=70.0,
        letter_grade="C-",
        strengths=["Good methodology", "Clear presentation"],
        areas_for_improvement=["Attention to detail", "Data verification"],
        overall_feedback="Good understanding of concepts, but need to be more thorough with data...",
        grading_timestamp=datetime.now().isoformat()
    )
    
    print("\n✅ Valid ExamGradingReport created:")
    print(f"Student: {report.student_name}")
    print(f"Grade: {report.letter_grade} ({report.overall_percentage}%)")
    print(f"Summary: {report.get_summary_stats()}")

