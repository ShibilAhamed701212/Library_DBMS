"""
validators.py
-------------
Input validation utilities for the application.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from email_validator import validate_email, EmailNotValidError

from backend.config.config import Config

class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

def validate_string(value: Any, field_name: str, min_length: int = 1, max_length: int = 255) -> str:
    """
    Validate a string value.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        The validated string
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)
    
    value = value.strip()
    length = len(value)
    
    if length < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters long", 
            field_name
        )
    
    if length > max_length:
        raise ValidationError(
            f"{field_name} must not exceed {max_length} characters", 
            field_name
        )
    
    return value

def validate_email_address(email: str) -> str:
    """
    Validate an email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email address
        
    Raises:
        ValidationError: If email is invalid
    """
    try:
        # Validate and normalize the email
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError as e:
        raise ValidationError("Invalid email address", "email") from e

def validate_password(password: str) -> str:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        The validated password
        
    Raises:
        ValidationError: If password doesn't meet requirements
    """
    if not password:
        raise ValidationError("Password is required", "password")
    
    # Custom strength checks: length, upper, lower, digit, special
    rules = {
        "length": len(password) >= 8,
        "upper": re.search(r"[A-Z]", password) is not None,
        "lower": re.search(r"[a-z]", password) is not None,
        "digit": re.search(r"\d", password) is not None,
        "special": re.search(r"[^A-Za-z0-9]", password) is not None,
    }

    if not all(rules.values()):
        missing = [name for name, ok in rules.items() if not ok]
        raise ValidationError(
            "Weak password: must be at least 8 chars and include upper, lower, digit, and special character",
            "password",
        )
    
    return password

def validate_date(date_str: str, date_format: str = "%Y-%m-%d") -> str:
    """
    Validate a date string.
    
    Args:
        date_str: Date string to validate
        date_format: Expected date format
        
    Returns:
        The validated date string
        
    Raises:
        ValidationError: If date is invalid or in wrong format
    """
    try:
        datetime.strptime(date_str, date_format)
        return date_str
    except ValueError as e:
        raise ValidationError(f"Invalid date format. Expected {date_format}", "date") from e

def validate_integer(value: Any, field_name: str, min_val: int = None, max_val: int = None) -> int:
    """
    Validate an integer value.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        
    Returns:
        The validated integer
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        num = int(value)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"{field_name} must be an integer", field_name) from e
    
    if min_val is not None and num < min_val:
        raise ValidationError(
            f"{field_name} must be at least {min_val}", 
            field_name
        )
    
    if max_val is not None and num > max_val:
        raise ValidationError(
            f"{field_name} must not exceed {max_val}", 
            field_name
        )
    
    return num

def validate_choice(value: Any, field_name: str, choices: list) -> Any:
    """
    Validate that a value is one of the allowed choices.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        choices: List of allowed values
        
    Returns:
        The validated value
        
    Raises:
        ValidationError: If value is not in choices
    """
    if value not in choices:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(map(str, choices))}",
            field_name
        )
    return value
