"""Get session output DTO."""
from .session_base import SessionBase
from typing import List
from ..analyses.analysis_detail import AnalysisDetail

class GetSessionOutput(SessionBase):
    """Output for GET /sessions/{id}."""
    analyses: List[AnalysisDetail] = []
