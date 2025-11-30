import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any


class GradingTools:
    """Collection of tools for the LLM grader to access data and resources."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize grading tools with data directory.
        
        Args:
            data_dir: Path to the data directory containing datasets and resources
        """
        self.data_dir = Path(data_dir)
        self.datasets_dir = self.data_dir / "datasets"
        self.resources_dir = self.data_dir / "class_resources"
        
        # Cache loaded files
        self._rubric_cache = None
        self._ground_truth_cache = None
        self._dataset_cache = {}
    
    def get_grading_rubric(self, question_number: int) -> Dict[str, Any]:
        """
        Get the grading rubric for a specific question.
        
        This tool provides point allocation breakdown, partial credit criteria,
        and common errors to check for when grading.
        
        Args:
            question_number (int): Question number from 1 to 10
            
        Returns:
            Dict[str, Any]: Dictionary containing grading rubric details
        """
        if self._rubric_cache is None:
            rubric_path = self.resources_dir / "grading_rubric.json"
            with open(rubric_path, 'r') as f:
                self._rubric_cache = json.load(f)
        
        # Find the question in the rubric
        for question in self._rubric_cache.get('questions', []):
            if question['question_number'] == question_number:
                return {
                    "question_number": question_number,
                    "points": question['points'],
                    "title": question['title'],
                    "correct_answer": question.get('correct_answer') or question.get('correct_answers'),
                    "full_credit_criteria": question['full_credit_criteria'],
                    "partial_credit": question['partial_credit'],
                    "common_errors": question['common_errors_to_check']
                }
        
        return {"error": f"Question {question_number} not found in rubric"}
    
    def get_ground_truth_answer(self, question_number: int) -> Dict[str, Any]:
        """
        Get the ground truth answer and solution for a specific question.
        
        Returns the correct answer, step-by-step methodology, and detailed
        calculation breakdown for grading reference.
        
        Args:
            question_number (int): Question number from 1 to 10
            
        Returns:
            Dict[str, Any]: Dictionary with correct answer and methodology
        """
        if self._ground_truth_cache is None:
            truth_path = self.resources_dir / "ground_truth_answers.json"
            with open(truth_path, 'r') as f:
                self._ground_truth_cache = json.load(f)
        
        # Find the question in ground truth
        for answer in self._ground_truth_cache.get('answers', []):
            if answer['question_number'] == question_number:
                return {
                    "question_number": question_number,
                    "title": answer['title'],
                    "correct_answer": answer['correct_answer'] or answer.get('correct_answers'),
                    "methodology": answer['methodology'],
                    "detailed_calculation": answer.get('detailed_calculation'),
                    "key_points": answer['key_points'],
                    "dataset_used": answer['dataset_used']
                }
        
        return {"error": f"Question {question_number} not found in ground truth"}
    
    def read_dataset(self, filename: str, num_rows: Optional[int] = None) -> str:
        """
        Read and display a CSV dataset.
        
        Use this to examine the structure and contents of datasets.
        
        Args:
            filename (str): Name of the CSV file (e.g., 'ecommerce_sales.csv')
            num_rows (int, optional): Limit number of rows to return
            
        Returns:
            str: String representation of the dataset
        """
        dataset_path = self.datasets_dir / filename
        
        if not dataset_path.exists():
            return f"Error: Dataset {filename} not found"
        
        try:
            df = pd.read_csv(dataset_path)
            
            if num_rows:
                df = df.head(num_rows)
            
            result = f"Dataset: {filename}\n"
            result += f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n"
            result += f"Columns: {', '.join(df.columns)}\n\n"
            result += df.to_string()
            
            return result
        except Exception as e:
            return f"Error reading {filename}: {str(e)}"
    
    def query_dataset(
        self, 
        filename: str, 
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        calculate: Optional[str] = None
    ) -> str:
        """
        Query a dataset with filters and calculations.
        
        This is the main tool for verifying student answers against actual data.
        Use filters like {'category': 'Electronics'} for exact match or
        {'age': {'gte': 18, 'lte': 30}} for range queries.
        
        Args:
            filename (str): CSV filename
            filters (dict, optional): Column:value pairs to filter by
            columns (list, optional): List of columns to return
            calculate (str, optional): Operation - 'count', 'sum', 'mean', 'max', 'min'
            
        Returns:
            str: Query results as string
        """
        dataset_path = self.datasets_dir / filename
        
        if not dataset_path.exists():
            return f"Error: Dataset {filename} not found"
        
        try:
            df = pd.read_csv(dataset_path)
            
            # Apply filters
            if filters:
                for col, value in filters.items():
                    if col not in df.columns:
                        return f"Error: Column '{col}' not found in {filename}"
                    
                    # Handle different filter types
                    if isinstance(value, dict):
                        # Range filters like {"gte": 18, "lte": 30}
                        if 'gte' in value:
                            df = df[df[col] >= value['gte']]
                        if 'lte' in value:
                            df = df[df[col] <= value['lte']]
                        if 'gt' in value:
                            df = df[df[col] > value['gt']]
                        if 'lt' in value:
                            df = df[df[col] < value['lt']]
                    else:
                        # Exact match filter
                        df = df[df[col] == value]
            
            # Select columns
            if columns:
                missing_cols = [c for c in columns if c not in df.columns]
                if missing_cols:
                    return f"Error: Columns not found: {missing_cols}"
                df = df[columns]
            
            # Perform calculation
            if calculate:
                if calculate == 'count':
                    result = f"Count: {len(df)} records"
                elif calculate == 'sum':
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    sums = df[numeric_cols].sum()
                    result = f"Sums:\n{sums.to_string()}"
                elif calculate == 'mean':
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    means = df[numeric_cols].mean()
                    result = f"Means:\n{means.to_string()}"
                elif calculate == 'max':
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    maxes = df[numeric_cols].max()
                    result = f"Maximums:\n{maxes.to_string()}"
                elif calculate == 'min':
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    mins = df[numeric_cols].min()
                    result = f"Minimums:\n{mins.to_string()}"
                else:
                    result = f"Unknown calculation: {calculate}"
            else:
                # Return filtered data
                result = f"Query Results ({len(df)} records):\n"
                result += df.to_string()
            
            return result
            
        except Exception as e:
            return f"Error querying {filename}: {str(e)}"
    
    def calculate_revenue(
        self,
        filename: str = "ecommerce_sales.csv",
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Calculate total revenue from sales data.
        
        Automatically handles quantity × unit_price calculation for each order.
        
        Args:
            filename (str): Sales dataset filename
            filters (dict, optional): Filters like category, status, date range
            
        Returns:
            str: Revenue calculation details
        """

        dataset_path = self.datasets_dir / filename
        
        if not dataset_path.exists():
            return f"Error: Dataset {filename} not found"
        
        try:
            df = pd.read_csv(dataset_path)
            
            # Apply filters
            if filters:
                for col, value in filters.items():
                    if col not in df.columns:
                        return f"Error: Column '{col}' not found"
                    df = df[df[col] == value]
            
            # Calculate revenue
            if 'quantity' in df.columns and 'unit_price' in df.columns:
                df['revenue'] = df['quantity'] * df['unit_price']
                total_revenue = df['revenue'].sum()
                
                result = f"Revenue Calculation:\n"
                result += f"Number of orders: {len(df)}\n"
                result += f"Total revenue: ${total_revenue:,.2f}\n\n"
                result += "Breakdown by order:\n"
                result += df[['order_id', 'quantity', 'unit_price', 'revenue']].to_string()
                
                return result
            else:
                return "Error: Dataset must have 'quantity' and 'unit_price' columns"
                
        except Exception as e:
            return f"Error calculating revenue: {str(e)}"
    
    def get_dataset_info(self, filename: str) -> str:
        """
        Get metadata and summary statistics for a dataset.
        
        Args:
            filename: Name of the CSV file
            
        Returns:
            String with dataset information
        """
        dataset_path = self.datasets_dir / filename
        
        if not dataset_path.exists():
            return f"Error: Dataset {filename} not found"
        
        try:
            df = pd.read_csv(dataset_path)
            
            result = f"Dataset: {filename}\n"
            result += f"{'='*60}\n\n"
            result += f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n\n"
            result += f"Columns:\n"
            for col in df.columns:
                dtype = df[col].dtype
                null_count = df[col].isnull().sum()
                result += f"  - {col} ({dtype})"
                if null_count > 0:
                    result += f" - {null_count} missing values"
                result += "\n"
            
            result += f"\nSummary Statistics:\n"
            result += df.describe().to_string()
            
            return result
            
        except Exception as e:
            return f"Error getting info for {filename}: {str(e)}"

