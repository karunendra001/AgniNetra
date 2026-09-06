from pydantic import BaseModel, Field


class Detection(BaseModel):
    """Exact field names the CRA frontend expects (see src/api/detections.js)."""

    id: int
    location: str
    lat: float
    lng: float
    classification: str
    confidence: float = Field(ge=0, le=100)
    brightness: float
    frp: float
    satellite: str
    time: str


class Stats(BaseModel):
    fire: int
    industrial: int
    persistent: int
    highConfidence: int
    total: int
    lastSync: str | None = None  # ISO UTC of last successful NASA FIRMS pull
