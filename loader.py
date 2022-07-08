from pathlib import Path
import pandas
from typing import List, Optional

from activityMatch import Activity, Player


def load_activities(path: Path) -> List[Activity]:
    # Loading the activities. The data must be in a .csv file with the following columns:
    # name : String with the name of the activity
    # capacity : Max number of players that can join the activity
    # start : When the activity starts, a datetime that can be parsed by pandas
    # end : When the activity ends

    activities_df = pandas.read_csv(path, delimiter=',', quotechar='"', parse_dates=['start', 'end'])
    return [
        Activity(act['name'], act['capacity'], act['start'], act['end'])
        for (_, act) in activities_df.iterrows()
    ]


def load_players(path: Path, activities: List[Activity]) -> List[Player]:
    # Loading the players and their wishes.
    # Must be a .csv file with the following columns :
    # name : Name of the player
    # wish <n> : Activity in rank <n> in their wishlist. These columns MUST be in the right order
    # max_games : max number of activities to participate

    def find_activity(name: str) -> Optional[Activity]:
        a = [act for act in activities if act.name == name]
        try:
            return a[0]
        except IndexError:
            raise ValueError(f"Could not find activity {name} in the activity list. Check your activity file.")

    players_df = pandas.read_csv(path, delimiter=',', quotechar='"')
    players: List[Player] = []
    wishes_columns: List[str] = [c for c in players_df.columns if c.startswith("wish")]
    print(f"Detected {len(wishes_columns)} columns containing wishes")

    for (_, p) in players_df.iterrows():
        # Convert the ranked names into a sorted list of Activities
        wishes = [find_activity(act) for act in p[wishes_columns] if not pandas.isna(act)]
        players.append(Player(p['name'], wishes))

    return players
