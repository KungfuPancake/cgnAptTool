from datetime import time, datetime
from dataclasses import dataclass


@dataclass
class DayRange:
    weekday: int
    start_time: time
    end_time: time


@dataclass
class Appointment:
    date: datetime
    date_raw: str
    duration: int
    location: str
    resources: str
    ws_id: str
