from pydantic import BaseModel


class BurnProjectResponse(BaseModel):
    candidate_count: int
