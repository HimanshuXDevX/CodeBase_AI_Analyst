from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum

class AnalysisType(str, Enum):
    GENERAL = "general"
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    QUALITY = "quality"
    PERFORMANCE = "performance"

class FileInfo(BaseModel):
    path: str
    content: str = Field(..., max_length=2000)
    size_kb: float

class RepositoryMetadata(BaseModel):
    full_name: str
    description: Optional[str] = None
    stars: int = Field(..., ge=0)
    language: Optional[str] = None
    default_branch: str = "main"

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None

class WebhookResponse(BaseModel):
    message: str
    event_type: Optional[str] = None
    repository: Optional[str] = None
    analysis_triggered: bool = False

class AnalysisRequest(BaseModel):
    repository: str = Field(..., min_length=1, description="GitHub repository URL")
    type: AnalysisType = Field(default=AnalysisType.GENERAL, description="Type of analysis to perform")
    
    @field_validator('repository')
    @classmethod
    def parse_repository(cls, v: str) -> str:
        v = v.rstrip('/')
        if 'github.com' in v:
            parts = v.split('github.com/')
            if len(parts) > 1:
                return parts[1].split('?')[0].split('#')[0]
        if '/' in v and not v.startswith('http'):
            return v
        raise ValueError("Invalid repository format. Use 'owner/repo' or full GitHub URL")

class AnalysisResponse(BaseModel):
    success: bool
    repository: str
    analysis_type: AnalysisType
    analysis: str
    files_analyzed: int = Field(..., ge=0)
    stars: int = Field(..., ge=0)
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    

class Config:
    use_enum_values = True