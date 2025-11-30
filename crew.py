"""
CrewAI Crew Configuration for LLM Grading System
=================================================

Orchestrates agents and tasks into a cohesive grading system.
"""

from crewai import Crew, Process
from agents import create_grader_agent, create_validation_agent
from tasks import create_grading_task, create_validation_task
from schemas import GradingResult
from guardrails import GradingGuardrails
import json
from typing import Dict, List, Tuple, Optional


class GradingCrew:
    """Manages the grading crew and workflow."""
    
    def __init__(
        self,
        model_name: str = "gpt-4",
        temperature: float = 0.1,
        enable_validation: bool = False,
        verbose: bool = True
    ):
        """
        Initialize the grading crew.
        
        Args:
            model_name: LLM model to use
            temperature: Temperature for generation
            enable_validation: Whether to use validation agent (slower but more thorough)
            verbose: Whether to print detailed logs
        """
        self.model_name = model_name
        self.temperature = temperature
        self.enable_validation = enable_validation
        self.verbose = verbose
        
        # Create agents
        self.grader_agent = create_grader_agent(
            model_name=model_name,
            temperature=temperature
        )
        
        if enable_validation:
            self.validation_agent = create_validation_agent(
                model_name=model_name,
                temperature=0.0  # Validation should be deterministic
            )
        
        # Initialize guardrails
        self.guardrails = GradingGuardrails()
    
    def grade_single_question(
        self,
        question_number: int,
        question_text: str,
        student_answer: str,
        dataset_file: str,
        student_id: Optional[str] = None
    ) -> Tuple[bool, GradingResult, List[str]]:
        """
        Grade a single question submission.
        
        Args:
            question_number: Question number (1-10)
            question_text: Full question text
            student_answer: Student's answer
            dataset_file: Dataset filename
            student_id: Optional student ID for rate limiting
            
        Returns:
            Tuple of (success, grading_result, messages)
        """
        
        messages = []
        
        # Step 1: Input validation
        submission = {
            'question_number': question_number,
            'student_answer': student_answer
        }
        
        valid, errors = self.guardrails.input_guards.validate_student_submission(submission)
        if not valid:
            messages.extend([f"❌ {err}" for err in errors])
            return False, self.guardrails.error_handler.create_fallback_result(
                question_number, student_answer, errors[0]
            ), messages
        
        # Step 2: Create grading task
        task = create_grading_task(
            agent=self.grader_agent,
            question_number=question_number,
            question_text=question_text,
            student_answer=student_answer,
            dataset_file=dataset_file
        )
        
        # Step 3: Create and run crew
        crew = Crew(
            agents=[self.grader_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose
        )
        
        try:
            # Execute grading
            result = crew.kickoff()
            
            # Parse result - CrewAI returns the Pydantic model directly
            if isinstance(result, GradingResult):
                grading_result = result
            elif isinstance(result, dict):
                grading_result = GradingResult(**result)
            elif isinstance(result, str):
                grading_result = GradingResult(**json.loads(result))
            else:
                # Try to convert to dict first
                result_dict = result.dict() if hasattr(result, 'dict') else dict(result)
                grading_result = GradingResult(**result_dict)
            
            messages.append(f"✅ Grading complete: {grading_result.points_earned}/{grading_result.points_possible} points")
            
            return True, grading_result, messages
            
        except Exception as e:
            messages.append(f"❌ Grading failed: {str(e)}")
            return False, self.guardrails.error_handler.create_fallback_result(
                question_number, student_answer, str(e)
            ), messages
    
    def grade_multiple_questions(
        self,
        submissions: List[Dict],
        student_id: Optional[str] = None
    ) -> Tuple[List[GradingResult], List[str]]:
        """
        Grade multiple questions.
        
        Args:
            submissions: List of dicts with question_number, question_text, 
                        student_answer, dataset_file
            student_id: Optional student ID
            
        Returns:
            Tuple of (grading_results, all_messages)
        """
        
        results = []
        all_messages = []
        
        for i, submission in enumerate(submissions):
            print(f"\n{'='*70}")
            print(f"Grading Question {submission['question_number']} ({i+1}/{len(submissions)})")
            print(f"{'='*70}\n")
            
            success, result, messages = self.grade_single_question(
                question_number=submission['question_number'],
                question_text=submission['question_text'],
                student_answer=submission['student_answer'],
                dataset_file=submission['dataset_file'],
                student_id=student_id
            )
            
            results.append(result)
            all_messages.extend(messages)
            
            # Print summary
            if success:
                print(f"✅ Grade: {result.points_earned}/{result.points_possible} points")
            else:
                print(f"❌ Grading failed, flagged for manual review")
        
        return results, all_messages
    
    def create_exam_report(
        self,
        results: List[GradingResult],
        student_name: str,
        exam_date: str
    ) -> Dict:
        """
        Create a complete exam grading report.
        
        Args:
            results: List of grading results
            student_name: Student's name
            exam_date: Exam date
            
        Returns:
            Complete exam report dict
        """
        
        total_earned = sum(r.points_earned for r in results)
        total_possible = sum(r.points_possible for r in results)
        percentage = (total_earned / total_possible * 100) if total_possible > 0 else 0
        
        # Determine letter grade
        if percentage >= 93:
            letter_grade = "A"
        elif percentage >= 90:
            letter_grade = "A-"
        elif percentage >= 87:
            letter_grade = "B+"
        elif percentage >= 83:
            letter_grade = "B"
        elif percentage >= 80:
            letter_grade = "B-"
        elif percentage >= 77:
            letter_grade = "C+"
        elif percentage >= 73:
            letter_grade = "C"
        elif percentage >= 70:
            letter_grade = "C-"
        elif percentage >= 60:
            letter_grade = "D"
        else:
            letter_grade = "F"
        
        # Identify strengths and weaknesses
        strengths = []
        areas_for_improvement = []
        
        for result in results:
            if result.points_earned >= 8:
                strengths.append(f"Strong performance on Q{result.question_number}")
            elif result.points_earned <= 5:
                areas_for_improvement.append(f"Review concepts from Q{result.question_number}")
        
        return {
            "student_name": student_name,
            "exam_date": exam_date,
            "total_questions": len(results),
            "total_points_earned": total_earned,
            "total_points_possible": total_possible,
            "percentage": round(percentage, 2),
            "letter_grade": letter_grade,
            "question_results": [r.dict() for r in results],
            "strengths": strengths if strengths else ["Consistent effort across all questions"],
            "areas_for_improvement": areas_for_improvement if areas_for_improvement else ["Continue current study approach"],
            "overall_feedback": f"You scored {total_earned}/{total_possible} points ({percentage:.1f}%). " +
                              (f"Good job! " if percentage >= 70 else "Consider reviewing the material. ") +
                              f"Focus on: {', '.join(areas_for_improvement[:2]) if areas_for_improvement else 'maintaining your performance'}."
        }


if __name__ == "__main__":
    # Test the crew
    print("Initializing Grading Crew...")
    crew_manager = GradingCrew(
        model_name="gpt-4",
        temperature=0.1,
        verbose=False
    )
    
    print("✅ Crew initialized")
    print(f"   Grader agent: {crew_manager.grader_agent.role}")
    print(f"   Guardrails: Enabled")
    print(f"   Validation: {'Enabled' if crew_manager.enable_validation else 'Disabled'}")

