from pydantic import BaseModel
from typing import List

class TeamData(BaseModel):
    TempoRating: float
    defRating: float
    offRating: float

class PredictModel (BaseModel):
    homeData: TeamData
    awayData: TeamData
    neutralSite: bool

class PredictModelList (BaseModel):
    games: List[PredictModel]
