from __future__ import annotations

import datetime
from typing import List, Dict

SLOT_TIMES = {
    'matin': ('08:00', '13:00'),
    'après-midi': ('13:00', '18:00'),
    'soir': ('19:00', '23:59')
}

WEEK_DAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

EVENT_DAY_START = 22


class TimeSlot:
    def __init__(self, day_name: str, day_nb: int, slot_name: str):
        self.day_name: str = day_name
        self.day_nb: int = day_nb
        self.slot_name: str = slot_name

        start, end = SLOT_TIMES[slot_name]
        self.start = datetime.datetime.fromisoformat("2022-08-" + str(self.day_nb) + 'T' + start)
        self.end = datetime.datetime.fromisoformat("2022-08-" + str(self.day_nb) + 'T' + end)

    def overlaps(self, other: TimeSlot) -> bool:
        if (self.start <= other.start) and (other.start < self.end):
            return True
        elif (other.start <= self.start) and (self.start < other.end):
            return True
        else:
            return False

    def __repr__(self):
        return f"{self.day_name} {self.day_nb} {self.slot_name}"

def generate_timeslots_from_column_names(column_names: List[str]) -> Dict[str, TimeSlot]:
    res = dict()
    for col in column_names:
        fields = col.split(' ')
        day_name = fields[0]
        day_nb = int(fields[1])
        slot_name = fields[2]

        slot = TimeSlot(day_name, day_nb, slot_name)
        res[col] = slot

    return res


def generate_all_timeslots() -> List[TimeSlot]:
    return [TimeSlot(name, nb, slot)
            for (name, nb) in zip(WEEK_DAYS, range(EVENT_DAY_START, EVENT_DAY_START + len(WEEK_DAYS)))
            for slot in SLOT_TIMES.keys()]
