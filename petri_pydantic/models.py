from typing import Self
from pydantic import BaseModel, AfterValidator, model_validator
from typing_extensions import Annotated

from petri_pydantic.views import *


class SignUp(BaseModel):
    username: Annotated[str, AfterValidator(validate_username)]
    email: Annotated[str,AfterValidator(validate_email_wrapper)]
    password: Annotated[str, AfterValidator(validate_password)]
    phone: Annotated[int, AfterValidator(validate_phone)]
    institype: str
    college: str
    gradyear: int
    stream: str

    @model_validator(mode='after')
    def check_validity(self) -> Self:
        if self.institype != "neither":
            if len(self.college) > 100:
                raise ValueError( "Institute Name must be at most 100 characters")
            elif not is_valid_string(self.college, r"^[a-zA-Z0-9_\s\.,\-]+$"):
                raise ValueError( "Institute Name can contain only {a-z, A-Z, 0-9, _, space, .}")
            elif self.institype == "college":
                if len(self.stream) > 100:
                    raise ValueError( "Degree must be at most 100 characters")
                elif not is_valid_string(self.stream, r"^[a-zA-Z0-9_\s\.\-,]+$"):
                    raise ValueError( "Degree can contain only {a-z, A-Z, 0-9, _, space, .}")
        return self
    
class EmailRequest(BaseModel):
    email: Annotated[str, AfterValidator(validate_email_wrapper)]

class NewPasswordRequest(BaseModel):
    new_password: Annotated[str, AfterValidator(validate_password)]

class PasswordRequest(BaseModel):
    password: Annotated[str, AfterValidator(validate_password)]

class LoginRequest(BaseModel):
    username: Annotated[str, AfterValidator(validate_email_wrapper)]
    password: Annotated[str, AfterValidator(validate_password)]

class AuthRequest(BaseModel):
    getUser: bool
    getEvents: bool

class EventPaid(BaseModel):
    participants: list[str]
    eventId: str
    transactionID: str
    CACode: str

class EventFree(BaseModel):
    participants: list[str]
    eventId: str

class Grievance(BaseModel):
    name: str
    email: Annotated[str, AfterValidator(validate_email_wrapper)]
    content: str

class CARequest(BaseModel):
    CACode: str