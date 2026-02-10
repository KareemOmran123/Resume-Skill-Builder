from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from ..models import IngestionQuery

class SourceAdapter(ABC):
    name: str

    @abstractmethod
    def fetch(self, q: IngestionQuery) -> List[Dict[str, Any]]:
        """Return raw postings as dicts. Normalization happens later."""
        raise NotImplementedError
