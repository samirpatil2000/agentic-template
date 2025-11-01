"""
Prompt templates for company analysis and research workflows.
"""

from typing import List

# System role definition
SYSTEM_ROLE = """You are an intelligent research and data enrichment assistant. Your goal is to help analyze organizations from their websites and prepare meaningful follow-up questions to capture more details."""

# Company summary fields to extract
SUMMARY_FIELDS = [
    "**Name**",
    "**Industry / Sector**",
    "**Products or Services Offered**",
    "**Target Customers / Market Segment**",
    "**Company Size (approximate if not explicitly mentioned)**",
    "**Headquarters Location**",
    "**Key Differentiators or Unique Selling Points**",
    "**Recent News or Notable Achievements (if identifiable)**"
]

# Question focus areas
QUESTION_AREAS = [
    "Their pain points or current challenges",
    "Their decision-making process",
    "Their current tools or workflows",
    "Their goals or upcoming initiatives",
    "How they measure success"
]

# JSON response schema
JSON_SCHEMA = """{
  "organization_summary": {
    "name": "",
    "industry": "",
    "products_or_services": "",
    "target_customers": "",
    "company_size": "",
    "headquarters": "",
    "unique_selling_points": "",
    "recent_news": ""
  },
  "follow_up_questions": ["question_1", "question_2", ...]
}"""


def get_company_summary_prompt(company_url: str) -> str:
    """
    Generate a comprehensive prompt for analyzing a company's website and creating follow-up questions.

    Args:
        company_url (str): The URL of the company's website to analyze

    Returns:
        str: A formatted prompt for company analysis
    """
    summary_fields_text = "\n".join([f"- {field}" for field in SUMMARY_FIELDS])
    question_areas_text = "\n".join([f"- {area}" for area in QUESTION_AREAS])

    prompt = f"""
        Given the company website URL: {company_url}

        1. Analyze the company's public website and extract a concise, structured summary including:
        {summary_fields_text}
        
        2. Based on this context, generate a set of 5–8 thoughtful follow-up questions that could be asked to someone from this company to deepen understanding. The questions should aim to learn about:
        {question_areas_text}
        
        3. Return the final response in **structured JSON format** with the following keys:
        
        {JSON_SCHEMA}
        
        Make sure the output is clean, concise, and ready to be stored in a database.
    """

    return prompt


def get_system_prompt() -> str:
    """
    Get the system role prompt for the company analysis assistant.

    Returns:
        str: The system role definition
    """
    return SYSTEM_ROLE


def get_summary_fields() -> List[str]:
    """
    Get the list of fields to extract in company summaries.

    Returns:
        List[str]: List of summary field names
    """
    return [field.strip("*") for field in SUMMARY_FIELDS]


def get_question_focus_areas() -> List[str]:
    """
    Get the list of areas that follow-up questions should focus on.

    Returns:
        List[str]: List of question focus areas
    """
    return QUESTION_AREAS
