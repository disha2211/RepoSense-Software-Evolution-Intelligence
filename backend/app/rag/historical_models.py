from pydantic import BaseModel, Field


class HistoricalEvent(BaseModel):
    commit_hash: str
    timestamp: str
    author: str
    message: str
    intent: str | None = None
    affected_files: list[str] = Field(
        default_factory=list
    )


class HistoricalResponse(BaseModel):
    answer: str
    confidence: str
    timeline: list[HistoricalEvent] = Field(
        default_factory=list
    )
    sources: list[str] = Field(
        default_factory=list
    )