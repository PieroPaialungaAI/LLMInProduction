"""
CrewAI Agent Configuration for LLM Grading System
==================================================

Defines the grader agent with its role, goal, backstory, and tools.
"""

from crewai import Agent
from langchain_openai import ChatOpenAI
from prompt import SYSTEM_PROMPT
from typing import Optional
import tool_functions


def create_grader_agent(
    model_name: str = "gpt-4",
    temperature: float = 0.1,
    tools_instance = None
) -> Agent:
    """
    Create the grader agent with full configuration.
    
    Args:
        model_name: LLM model to use
        temperature: Temperature for generation (lower = more deterministic)
        tools_instance: Ignored (for backwards compatibility)
        
    Returns:
        Configured CrewAI Agent
    """
    
    # Create LLM
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature
    )
    
    # Use standalone functions as tools
    tools_list = [
        tool_functions.get_grading_rubric,
        tool_functions.get_ground_truth_answer,
        tool_functions.read_dataset,
        tool_functions.query_electronics_orders,
        tool_functions.calculate_electronics_revenue,
        tool_functions.get_customer_age_groups,
        tool_functions.get_ab_test_conversions
    ]
    
    # Create the agent
    agent = Agent(
        role="Expert Data Science Grader",
        goal="Grade student data science exam submissions accurately and fairly by verifying answers against actual datasets",
        backstory=SYSTEM_PROMPT,
        tools=tools_list,
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15
    )
    
    return agent


def create_validation_agent(
    model_name: str = "gpt-4",
    temperature: float = 0.0
) -> Agent:
    """
    Create a validation agent to double-check grading results.
    
    This agent reviews the grader's output for consistency and fairness.
    
    Args:
        model_name: LLM model to use
        temperature: Temperature for generation
        
    Returns:
        Configured CrewAI Agent
    """
    
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature
    )
    
    agent = Agent(
        role="Grading Quality Reviewer",
        goal="Validate grading results for consistency, fairness, and policy compliance",
        backstory="""You are a senior educator with 15+ years of experience reviewing 
        grading decisions. Your job is to ensure that grades are:
        1. Internally consistent (points match breakdown, feedback matches score)
        2. Fair and unbiased
        3. Following all grading policies
        4. Providing constructive feedback to students
        
        You flag any issues but do not change grades yourself.""",
        tools=[],  # No tools needed, just reviews the JSON output
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    return agent


if __name__ == "__main__":
    # Test agent creation
    print("Creating grader agent...")
    agent = create_grader_agent()
    print(f"✅ Agent created: {agent.role}")
    print(f"   Goal: {agent.goal}")
    print(f"   Tools: {len(agent.tools)} tools available")

