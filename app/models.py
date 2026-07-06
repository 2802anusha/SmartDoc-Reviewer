from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid
import json


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ReviewJob(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    pr_url: str
    status: str = Field(default="pending")
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewReport(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    job_id: str = Field(foreign_key="reviewjob.id")
    pr_url: str
    security_findings: str = Field(default="[]")
    style_findings: str = Field(default="[]")
    logic_findings: str = Field(default="[]")
    summary: str = Field(default="")
    overall_score: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_security(self) -> list:
        return json.loads(self.security_findings)

    def get_style(self) -> list:
        return json.loads(self.style_findings)

    def get_logic(self) -> list:
        return json.loads(self.logic_findings)


class ReviewRequest(SQLModel):
    pr_url: str


class ReviewJobResponse(SQLModel):
    id: str
    pr_url: str
    status: str
    created_at: datetime


class ReviewReportResponse(SQLModel):
    job_id: str
    pr_url: str
    security_findings: list
    style_findings: list
    logic_findings: list
    summary: str
    overall_score: int