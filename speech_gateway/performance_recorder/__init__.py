from abc import ABC, abstractmethod
from dataclasses import dataclass


class PerformanceRecorder(ABC):
    @abstractmethod
    def record(
        self,
        *,
        process_id: str,
        source: str = None,
        text: str = None,
        audio_format: str = None,
        cached: int = 0,
        elapsed: float = None,
    ):
        pass

    @abstractmethod
    def close(self):
        pass


@dataclass
class PerformanceRecord:
    process_id: str
    source: str = None
    text: str = None
    audio_format: str = None
    cached: int = 0,
    elapsed: float = None,


from .sqlite import SQLitePerformanceRecorder
