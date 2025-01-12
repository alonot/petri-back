# this module contains all the validators

import re

from pydantic import validate_email

def is_valid_string(s, pattern):
    return bool(re.match(pattern, s))

def validate_username(value: str) -> str:
    if not (1 <= len(value) <= 25):
        raise ValueError(f"Username:{value}'s length must be between 1 and 25 characters")
    elif not is_valid_string(value, r"^[a-zA-Z0-9_\s]+$"):
        raise ValueError("Wrong Username format: can contain only {a-z, A-Z, 0-9, _, space}")

    return value

def validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    elif not is_valid_string(value, r"^[a-zA-Z0-9_\s\.]+$"):
        raise ValueError("Password can contain only {a-z, A-Z, 0-9, _, space, .}")
    return value

def validate_phone(value: int) -> int:
    if not (1000000000 <= value <= 9999999999):
        raise ValueError("Phone Number must be of length: 10")
    return value

def validate_email_wrapper(value: str) -> str:
    return validate_email(value)[1]