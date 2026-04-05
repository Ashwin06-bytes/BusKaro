from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class BaseAdapter(ABC):
    source_name = "base"

    def __init__(self, is_dummy: bool = True):
        self.is_dummy = is_dummy

    @abstractmethod
    def fetch(self, origin: str, destination: str, date: str) -> List[Dict[str, Any]]:
        """
        Fetch results for the given route and date.
        Must return a list of normalized dictionaries.
        """
        pass

    def normalize(self, raw_data: Any) -> Dict[str, Any]:
        """
        Normalize internal/external raw data into the standard schema.
        """
        return raw_data
