from pathlib import Path
import pandas
import datetime
from typing import List, Optional, Dict

from activityMatch import Activity, Player, Constraint


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

    def find_activities(name: str) -> List[Activity]:
        a = [act for act in activities if act.name == name]
        try:
            return a
        except IndexError:
            print(f"WARNING. Could not find activity {name} in the activity list. Check your activity file.")
            return []

    players_df = pandas.read_csv(path, delimiter=',', quotechar='"')
    players: List[Player] = []
    wishes_columns: List[str] = [c for c in players_df.columns if c.startswith("wish")]
    print(f"Detected {len(wishes_columns)} columns containing wishes")

    slot_names = {
        'matin': ('08:00', '13:00'),
        'après-midi': ('13:00', '18:00'),
        'soir': ('18:00', '23:59')
    }
    day_columns: list[str] = [c for c in players_df.columns if
                              c.split(' ')[0] in ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi',
                                                  'Dimanche']]
    time_slots = dict()

    for slot in day_columns:
        day = slot.split(' ')[1]
        start, end = slot_names[slot.split(' ')[-1]]
        start = datetime.datetime.fromisoformat("2022-08-" + day + 'T' + start)
        end = datetime.datetime.fromisoformat("2022-08-" + day + 'T' + end)
        time_slots[slot] = (start, end)

    blacklist: Dict[str, List[str]] = {}
    for (_, p) in players_df.iterrows():
        if pandas.isna(p['name']):
            continue

        name = p['name'].strip()
        print(f"Processing player {name}")
        # Convert the ranked names into a sorted list of Activities
        # Be careful, players rank a given activity but one activity may have multiple sessions. So we get all the
        # activities with this name and add them in order to the wishlist
        wishes = []
        for act_name in p[wishes_columns]:
            if pandas.isna(act_name):
                continue
            wishes.extend(find_activities(act_name.strip()))

        max_games = p['max_games'] if not pandas.isna(p['max_games']) else None
        blacklist[name] = str(p['blacklist']).strip().split(';')

        # Load time availability and remove wishes when the player is not available
        for (col, (start, end)) in time_slots.items():
            # If nothing written in the column, they are not available at this time.
            if pandas.isna(p[col]):
                removes = [w.name for w in wishes if w.overlaps(start, end)]
                if removes:
                    print(f"{name} is not available {col}. Removing impossible wishes")
                    print(f"Removed : ")
                    for a in removes:
                        print(f'- {a}')
                wishes = [w for w in wishes if not w.overlaps(start, end)]

        # Generate constraints
        constraints_names = {
            "Jouer deux jeux dans la même journée": Constraint.TWO_SAME_DAY,
            "Jouer un soir et le lendemain matin": Constraint.NIGHT_THEN_MORNING,
            "Jouer deux jours consécutifs": Constraint.TWO_CONSECUTIVE_DAYS,
            "Jouer trois jours consécutifs": Constraint.THREE_CONSECUTIVE_DAYS,
            "Jouer plus de trois jours consécutifs": Constraint.MORE_CONSECUTIVE_DAYS
        }
        constraints = set(cons for (col, cons) in constraints_names.items() if pandas.isna(p[col]))

        players.append(Player(name, wishes, max_activities=max_games, constraints=constraints))

    # Now that the players are created, populate the blacklists
    for (name, bl_names) in blacklist.items():
        player = [pl for pl in players if pl.name == name][0]
        bl = [find_player_by_name(b, players) for b in bl_names if b != '' and b != 'nan']

        for pl in bl:
            if pl is not None:
                player.add_blacklist_player(pl)

    return players


def find_player_by_name(name: str, players: List[Player]) -> Optional[Player]:
    p = [pl for pl in players if pl.name == name]
    if not p:
        print(f"Could not find player {name}")
        return None
    else:
        return p[0]
