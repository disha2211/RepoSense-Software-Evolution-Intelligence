from pydantic import BaseModel, Field


class ImpactComponent(BaseModel):
    id: str
    name: str
    relationship: str
    direction: str


class ImpactResponse(BaseModel):
    target: str
    impact_level: str
    summary: str
    affected_components: list[ImpactComponent] = Field(
        default_factory=list
    )
    reasoning: list[str] = Field(
        default_factory=list
    )
    sources: list[str] = Field(
        default_factory=list
    )