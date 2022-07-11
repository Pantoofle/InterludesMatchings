from pathlib import Path
import pandas
from typing import List, Optional, Dict

from activityMatch import Activity, Player


def load_activities(path: Path) -> List[Activity]:
    # Loading the activities. The data must be in a .csv file with the following columns:
    # name : String with the name of the activity
    # capacity : Max number of players that can join the activity
    # start : When the activity starts, a datetime that can be parsed by pandas
    # end : When the activity ends

    activities_df = pandas.read_csv(path, delimiter=',', quotechar='"', parse_dates=['start', 'end'])
    return [
        Activity(act['name'].strip(), act['capacity'], act['start'], act['end'])
        for (_, act) in activities_df.iterrows() if not pandas.isna(act['name'])
    ]


def load_players(path: Path, activities: List[Activity]) -> List[Player]:
    # Loading the players and their wishes.
    # Must be a .csv file with the following columns :
    # name : Name of the player
    # wish <n> : Activity in rank <n> in their wishlist. These columns MUST be in the right order
    # max_games : max number of activities to participate

    # TODO: Manage players disponibility during the week to remove wishes for activities when the player is not there

    def find_activity(name: str) -> Optional[Activity]:
        a = [act for act in activities if act.name == name]
        try:
            return a[0]
        except IndexError:
            print(f"WARNING. Could not find activity {name} in the activity list. Check your activity file.")
            return None

    players_df = pandas.read_csv(path, delimiter=',', quotechar='"')
    players: List[Player] = []
    wishes_columns: List[str] = [c for c in players_df.columns if c.startswith("wish")]
    print(f"Detected {len(wishes_columns)} columns containing wishes")

    blacklist: Dict[str, List[str]] = {}
    for (_, p) in players_df.iterrows():
        if pandas.isna(p['name']):
            continue

        print(f"Processing player {p['name']}")
        # Convert the ranked names into a sorted list of Activities
        wishes = [find_activity(act.strip()) for act in p[wishes_columns] if not pandas.isna(act)]
        wishes = [w for w in wishes if w is not None]
        max_games = p['max_games'] if not pandas.isna(p['max_games']) else None
        blacklist[p['name']] = str(p['blacklist']).strip().split(';')

        players.append(Player(p['name'], wishes, max_activities=max_games))

    # Now that the players are created, populate the blacklists
    for (name, bl_names) in blacklist.items():
        player = [pl for pl in players if pl.name == name][0]
        bl = [find_player_by_name(b, players) for b in bl_names if b != '' and b != 'nan']

        for pl in bl:
            if pl is not None:
                player.add_blacklist_player(pl)

    return players


def find_player_by_name(name:str, players: List[Player]) -> Optional[Player]:
    p = [pl for pl in players if pl.name == name]
    if not p:
        print(f"Could not find player {name}")
        return None
    else:
        return p[0]

