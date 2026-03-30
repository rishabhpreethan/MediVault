from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    message: str


class SuccessResponse(BaseModel):
    message: str
