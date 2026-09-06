import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central config, read from environment / .env file."""

    def __init__(self):
        self.firms_map_key: str = os.getenv("FIRMS_MAP_KEY", "")
        self.firms_sources: list[str] = [
            s.strip()
            for s in os.getenv("FIRMS_SOURCES", "VIIRS_SNPP_NRT,VIIRS_NOAA20_NRT").split(",")
            if s.strip()
        ]
        self.firms_day_range: int = int(os.getenv("FIRMS_DAY_RANGE", "7"))
        # west,south,east,north
        bbox = os.getenv("FIRMS_BBOX", "68.0,6.0,97.5,35.5")
        w, s, e, n = (float(x) for x in bbox.split(","))
        self.firms_bbox: tuple[float, float, float, float] = (w, s, e, n)

        self.ingest_interval_minutes: int = int(os.getenv("INGEST_INTERVAL_MINUTES", "10"))

        self.use_ml_model: bool = os.getenv("USE_ML_MODEL", "false").lower() == "true"
        self.model_path: str = os.getenv("MODEL_PATH", "ml/model.pkl")

        self.db_path: str = os.getenv("DB_PATH", "data/fires.db")
        self.cors_origins: list[str] = [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ]

    @property
    def firms_configured(self) -> bool:
        return bool(self.firms_map_key)


settings = Settings()
