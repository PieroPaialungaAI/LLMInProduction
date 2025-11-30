"""
Guardrails and Validation for LLM Grading System
=================================================

Guardrails ensure reliability and safety by:
1. Validating inputs before processing
2. Validating LLM outputs before use
3. Enforcing business rules
4. Handling errors gracefully
5. Preventing system abuse
"""

import json
from typing import Dict, List, Tuple, Optional, Any
from pydantic import ValidationError
from schemas import GradingResult, ExamGradingReport
from datetime import datetime


class InputGuardrails:
    """Validate student submissions before processing."""
    
    @staticmethod
    def validate_student_submission(submission: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a student submission before grading.
        
        Args:
            submission: Student's answer submission
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        required_fields = ['question_number', 'student_answer']
        for field in required_fields:
            if field not in submission or submission[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Validate question number
        if 'question_number' in submission:
            qnum = submission['question_number']
            if not isinstance(qnum, int) or qnum < 1 or qnum > 10:
                errors.append(f"Invalid question_number: must be integer 1-10, got {qnum}")
        
        # Validate answer is not empty
        if 'student_answer' in submission:
            answer = submission['student_answer']
            if isinstance(answer, str) and len(answer.strip()) == 0:
                errors.append("student_answer cannot be empty")
            elif answer == "" or answer is None:
                errors.append("student_answer is missing or None")
        
        # Check answer length (prevent abuse)
        if 'student_answer' in submission:
            answer_str = str(submission['student_answer'])
            if len(answer_str) > 5000:
                errors.append(f"student_answer too long ({len(answer_str)} chars, max 5000)")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_student_answer(answer: str) -> str:
        """
        Sanitize student answer to remove potentially harmful content.
        
        Args:
            answer: Raw student answer
            
        Returns:
            Sanitized answer
        """
        # Remove potential prompt injection attempts
        dangerous_patterns = [
            "ignore previous instructions",
            "disregard all",
            "forget everything",
            "system:",
            "assistant:",
        ]
        
        sanitized = answer
        for pattern in dangerous_patterns:
            if pattern.lower() in sanitized.lower():
                # Flag but don't remove - let human review
                sanitized = f"[FLAGGED: potential prompt injection] {sanitized}"
                break
        
        return sanitized.strip()


class OutputGuardrails:
    """Validate LLM outputs before accepting them."""
    
    @staticmethod
    def validate_llm_response(
        response: Dict[str, Any],
        question_number: int
    ) -> Tuple[bool, List[str], Optional[GradingResult]]:
        """
        Validate LLM grading response.
        
        Args:
            response: LLM's JSON response
            question_number: Expected question number
            
        Returns:
            Tuple of (is_valid, error_messages, parsed_result)
        """
        errors = []
        
        # Try to parse as GradingResult
        try:
            result = GradingResult(**response)
        except ValidationError as e:
            errors.append(f"Pydantic validation failed: {str(e)}")
            return False, errors, None
        except Exception as e:
            errors.append(f"Failed to parse response: {str(e)}")
            return False, errors, None
        
        # Verify question number matches
        if result.question_number != question_number:
            errors.append(
                f"Question number mismatch: expected {question_number}, "
                f"got {result.question_number}"
            )
        
        # Verify points are logical
        if result.points_earned > result.points_possible:
            errors.append(
                f"Points earned ({result.points_earned}) exceeds "
                f"points possible ({result.points_possible})"
            )
        
        # Verify breakdown sums correctly
        breakdown_sum = sum(result.points_breakdown.values())
        if abs(breakdown_sum - result.points_earned) > 0.01:
            errors.append(
                f"Points breakdown ({breakdown_sum}) doesn't match "
                f"points earned ({result.points_earned})"
            )
        
        # Check feedback quality
        if len(result.feedback) < 20:
            errors.append(f"Feedback too short ({len(result.feedback)} chars, min 20)")
        
        # Check for placeholder/template text
        placeholder_indicators = [
            "[insert",
            "TODO",
            "FIXME",
            "xxx",
            "...",
        ]
        for indicator in placeholder_indicators:
            if indicator.lower() in result.feedback.lower():
                errors.append(f"Feedback contains placeholder text: {indicator}")
        
        return len(errors) == 0, errors, result
    
    @staticmethod
    def check_consistency(result: GradingResult) -> Tuple[bool, List[str]]:
        """
        Check internal consistency of grading result.
        
        Args:
            result: Parsed grading result
            
        Returns:
            Tuple of (is_consistent, warning_messages)
        """
        warnings = []
        
        # If marked correct, points should be high
        if result.is_correct and result.points_earned < 8:
            warnings.append(
                f"Marked as correct but only {result.points_earned}/10 points - "
                "should be at least 8"
            )
        
        # If marked incorrect, should have errors listed
        if not result.is_correct and len(result.specific_errors) == 0:
            warnings.append(
                "Marked as incorrect but no specific_errors provided"
            )
        
        # If error_type is no_error, should be marked correct
        if result.error_type == "no_error" and not result.is_correct:
            warnings.append(
                "error_type is 'no_error' but is_correct is False"
            )
        
        # If points earned is 0, breakdown should all be 0
        if result.points_earned == 0:
            if any(v > 0 for v in result.points_breakdown.values()):
                warnings.append(
                    "Points earned is 0 but breakdown has non-zero values"
                )
        
        return len(warnings) == 0, warnings


class BusinessRulesGuardrails:
    """Enforce business rules and policies."""
    
    @staticmethod
    def enforce_grading_policies(result: GradingResult) -> Tuple[bool, List[str]]:
        """
        Enforce grading policies.
        
        Args:
            result: Grading result to check
            
        Returns:
            Tuple of (compliant, policy_violations)
        """
        violations = []
        
        # Policy 1: Partial credit must be awarded if methodology is correct
        if result.error_type == "wrong_calculation":
            if result.points_breakdown.get("showing_work", 0) == 0:
                violations.append(
                    "Policy violation: Wrong calculation with no partial credit "
                    "for methodology"
                )
        
        # Policy 2: Minimum feedback length
        if result.points_earned < result.points_possible:
            if len(result.feedback) < 50:
                violations.append(
                    f"Policy violation: Incorrect answer requires detailed feedback "
                    f"(min 50 chars, got {len(result.feedback)})"
                )
        
        # Policy 3: Must reference data when available
        if result.error_type in ["wrong_calculation", "missing_data"]:
            if len(result.data_references) == 0:
                violations.append(
                    "Policy violation: Data-related error must include data_references"
                )
        
        # Policy 4: Zero points requires justification
        if result.points_earned == 0:
            if len(result.specific_errors) < 2:
                violations.append(
                    "Policy violation: Zero points requires at least 2 specific errors"
                )
        
        return len(violations) == 0, violations
    
    @staticmethod
    def check_grade_inflation(results: List[GradingResult]) -> Tuple[bool, str]:
        """
        Check for grade inflation across multiple questions.
        
        Args:
            results: List of grading results
            
        Returns:
            Tuple of (acceptable, message)
        """
        if len(results) == 0:
            return True, "No results to check"
        
        avg_score = sum(r.points_earned for r in results) / len(results)
        perfect_scores = sum(1 for r in results if r.points_earned == r.points_possible)
        perfect_rate = perfect_scores / len(results)
        
        # Warning if average is suspiciously high
        if avg_score > 9.5 and len(results) > 3:
            return False, f"Possible grade inflation: avg score {avg_score:.1f}/10"
        
        # Warning if too many perfect scores
        if perfect_rate > 0.8 and len(results) > 5:
            return False, f"Possible grade inflation: {perfect_rate*100:.0f}% perfect scores"
        
        return True, f"Grade distribution acceptable (avg: {avg_score:.1f}/10)"


class ErrorHandlingGuardrails:
    """Handle errors and provide fallbacks."""
    
    @staticmethod
    def create_fallback_result(
        question_number: int,
        student_answer: str,
        error_message: str
    ) -> GradingResult:
        """
        Create a fallback grading result when LLM fails.
        
        Args:
            question_number: Question number
            student_answer: Student's answer
            error_message: Error that occurred
            
        Returns:
            Fallback GradingResult for manual review
        """
        return GradingResult(
            question_number=question_number,
            points_earned=0.0,
            points_possible=10,
            is_correct=False,
            student_answer=student_answer,
            correct_answer="[REQUIRES MANUAL REVIEW]",
            points_breakdown={
                "correct_answer": 0,
                "showing_work": 0,
                "interpretation": 0
            },
            error_type="incomplete_work",
            specific_errors=[
                "Automated grading failed",
                f"Error: {error_message}",
                "This submission requires manual review"
            ],
            what_was_correct=[],
            feedback=f"""This submission could not be automatically graded due to a system error.

Error details: {error_message}

This answer has been flagged for manual review by an instructor. You will receive 
your grade and feedback within 24 hours.

If you believe this is an error, please contact your instructor.""",
            data_references=["[MANUAL REVIEW REQUIRED]"]
        )
    
    @staticmethod
    def should_retry(
        attempt_number: int,
        error_type: str,
        max_retries: int = 3
    ) -> bool:
        """
        Determine if we should retry after an error.
        
        Args:
            attempt_number: Current attempt number
            error_type: Type of error encountered
            max_retries: Maximum retry attempts
            
        Returns:
            Whether to retry
        """
        # Don't retry validation errors (bad student input)
        if error_type in ["validation_error", "invalid_input"]:
            return False
        
        # Don't retry if we've hit max attempts
        if attempt_number >= max_retries:
            return False
        
        # Retry for LLM errors, network errors, etc.
        return error_type in [
            "llm_error",
            "network_error",
            "timeout_error",
            "rate_limit_error"
        ]


class RateLimitGuardrails:
    """Prevent abuse through rate limiting."""
    
    def __init__(self):
        self.submission_history: Dict[str, List[datetime]] = {}
    
    def check_rate_limit(
        self,
        student_id: str,
        max_submissions_per_hour: int = 20
    ) -> Tuple[bool, str]:
        """
        Check if student has exceeded rate limits.
        
        Args:
            student_id: Identifier for the student
            max_submissions_per_hour: Maximum submissions allowed per hour
            
        Returns:
            Tuple of (allowed, message)
        """
        now = datetime.now()
        hour_ago = datetime.now().timestamp() - 3600
        
        # Get recent submissions for this student
        if student_id not in self.submission_history:
            self.submission_history[student_id] = []
        
        # Filter to submissions in last hour
        recent = [
            ts for ts in self.submission_history[student_id]
            if ts.timestamp() > hour_ago
        ]
        
        # Check limit
        if len(recent) >= max_submissions_per_hour:
            return False, f"Rate limit exceeded: {len(recent)} submissions in last hour (max {max_submissions_per_hour})"
        
        # Record this submission
        self.submission_history[student_id].append(now)
        
        return True, f"Rate limit OK: {len(recent)+1}/{max_submissions_per_hour} submissions this hour"


class GradingGuardrails:
    """Complete guardrail system for grading."""
    
    def __init__(self):
        self.input_guards = InputGuardrails()
        self.output_guards = OutputGuardrails()
        self.business_rules = BusinessRulesGuardrails()
        self.error_handler = ErrorHandlingGuardrails()
        self.rate_limiter = RateLimitGuardrails()
    
    def validate_and_grade(
        self,
        submission: Dict[str, Any],
        llm_response: Dict[str, Any],
        student_id: Optional[str] = None
    ) -> Tuple[bool, GradingResult, List[str]]:
        """
        Complete validation pipeline.
        
        Args:
            submission: Student submission
            llm_response: LLM's grading response
            student_id: Optional student identifier for rate limiting
            
        Returns:
            Tuple of (success, result, warnings_and_errors)
        """
        messages = []
        
        # Step 1: Rate limiting (if student_id provided)
        if student_id:
            allowed, msg = self.rate_limiter.check_rate_limit(student_id)
            if not allowed:
                messages.append(f"❌ {msg}")
                return False, self.error_handler.create_fallback_result(
                    submission.get('question_number', 0),
                    str(submission.get('student_answer', '')),
                    "Rate limit exceeded"
                ), messages
        
        # Step 2: Input validation
        valid_input, input_errors = self.input_guards.validate_student_submission(submission)
        if not valid_input:
            messages.extend([f"❌ Input: {err}" for err in input_errors])
            return False, self.error_handler.create_fallback_result(
                submission.get('question_number', 0),
                str(submission.get('student_answer', '')),
                f"Invalid submission: {input_errors[0]}"
            ), messages
        
        messages.append("✅ Input validation passed")
        
        # Step 3: Output validation
        valid_output, output_errors, result = self.output_guards.validate_llm_response(
            llm_response,
            submission['question_number']
        )
        
        if not valid_output or result is None:
            messages.extend([f"❌ Output: {err}" for err in output_errors])
            return False, self.error_handler.create_fallback_result(
                submission['question_number'],
                submission['student_answer'],
                f"Invalid LLM response: {output_errors[0]}"
            ), messages
        
        messages.append("✅ Output validation passed")
        
        # Step 4: Consistency checks
        consistent, consistency_warnings = self.output_guards.check_consistency(result)
        if not consistent:
            messages.extend([f"⚠️  Consistency: {warn}" for warn in consistency_warnings])
        
        # Step 5: Business rules
        compliant, violations = self.business_rules.enforce_grading_policies(result)
        if not compliant:
            messages.extend([f"⚠️  Policy: {viol}" for viol in violations])
        
        # Success
        messages.append(f"✅ Grading complete: {result.points_earned}/{result.points_possible} points")
        
        return True, result, messages


if __name__ == "__main__":
    # Test guardrails
    print("Testing Guardrails\n" + "="*70 + "\n")
    
    # Test 1: Input validation
    print("1. Input Validation:")
    submission = {
        "question_number": 1,
        "student_answer": "$6,500"
    }
    valid, errors = InputGuardrails.validate_student_submission(submission)
    print(f"   Valid: {valid}, Errors: {errors}")
    
    # Test 2: Invalid input
    print("\n2. Invalid Input (missing answer):")
    bad_submission = {"question_number": 1}
    valid, errors = InputGuardrails.validate_student_submission(bad_submission)
    print(f"   Valid: {valid}, Errors: {errors}")
    
    # Test 3: Output validation
    print("\n3. Output Validation:")
    llm_response = {
        "question_number": 1,
        "points_earned": 7.0,
        "points_possible": 10,
        "is_correct": False,
        "student_answer": "$6,500",
        "correct_answer": "$7,398.53",
        "points_breakdown": {
            "correct_answer": 3,
            "showing_work": 2,
            "interpretation": 2
        },
        "error_type": "wrong_calculation",
        "specific_errors": ["Missed orders"],
        "what_was_correct": ["Good methodology"],
        "feedback": "Your answer is close but you missed some orders in the dataset.",
        "data_references": ["ecommerce_sales.csv"]
    }
    valid, errors, result = OutputGuardrails.validate_llm_response(llm_response, 1)
    print(f"   Valid: {valid}, Errors: {errors}")
    
    print("\n" + "="*70)
    print("Guardrails working correctly!")

