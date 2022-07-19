from __future__ import annotations

from typing import List, Dict, Optional, Tuple, Iterator, Set
from matching.games import HospitalResident
import random
import datetime

from timeSlots import TimeSlot, generate_all_timeslots, SLOT_TIMES


class Activity:
    ACTIVE_ACTIVITIES = 0

    def __init__(self, name: str, capacity: int, start: datetime.datetime, end: datetime.datetime):
        # Auto number the activities
        self.id = Activity.ACTIVE_ACTIVITIES
        Activity.ACTIVE_ACTIVITIES += 1

        self.name: str = name
        self.capacity: int = capacity
        self.start: datetime.datetime = start
        self.end: datetime.datetime = end

        self.players: List[Player] = []

    def __repr__(self):
        return f"{self.id} | {self.name} | {len(self.players)} / {self.capacity} players | {self.start} - {self.end}"

    def overlaps(self, start: datetime.datetime, end: datetime.datetime) -> bool:
        if (self.start <= start) and (start < self.end):
            return True
        elif (start <= self.start) and (self.start < end):
            return True
        else:
            return False

    def breaks_constraint(self, cast: List[Activity], constraint: Constraint) -> bool:
        if constraint == Constraint.TWO_SAME_DAY:
            return self.start.date() in [a.start.date() for a in cast]
        elif constraint == Constraint.NIGHT_THEN_MORNING:
            for act in cast:
                # For each activity, check if the first one starts after the beginning of "soir"
                # the second one starts before the end of "matin"
                # and they are on two consecutive days
                first = min(self.start, act.start)
                last = max(self.start, act.start)
                if (first.time() >= datetime.time.fromisoformat(SLOT_TIMES['soir'][0])) and \
                    (last.time() <= datetime.time.fromisoformat(SLOT_TIMES['matin'][1])) and \
                        (first.date() + datetime.timedelta(days=1) == last.date()):
                    return True
            return False
        elif constraint == Constraint.TWO_CONSECUTIVE_DAYS:
            return any([abs((a.start.date() - self.start.date()).days) == 1 for a in cast])
        elif constraint == Constraint.THREE_CONSECUTIVE_DAYS:
            days_played = set([a.start.date() for a in cast] + [self.start.date()])
            days_played = sorted(list(days_played))
            return any(((b - a).days == 1) and
                       ((c-b).days == 1) for (a, b, c) in window(days_played, 3))
        elif constraint == Constraint.MORE_CONSECUTIVE_DAYS:
            days_played = set([a.start.date() for a in cast] + [self.start.date()])
            days_played = sorted(list(days_played))
            return any(((b - a).days == 1) and
                       ((c - b).days == 1) and
                       ((d - c).days == 1) for (a, b, c, d) in window(days_played, 4))
        else:
            raise ValueError("Unknown Constraint")

    def conflicts_with(self, other: Activity, player: Optional[Player] = None) -> bool:
        if player is None:
            return self.overlaps(other.start, other.end)
        else:
            return any(self.breaks_constraint(player.activities, c) for c in player.constraints) \
                   or self.overlaps(other.start, other.end)

        # If we gave a specific player, we need to check its custom constraints.

    #def find_conflicting_activities(self, activities: List[Activity], player: Optional[Player] = None) -> List[Activity]:
    #    return [a for a in activities if self.conflicts_with(a, player=player)]

    def is_full(self) -> bool:
        return len(self.players) >= self.capacity

    def add_player(self, player: Player) -> None:
        self.players.append(player)

    def remove_player(self, player: Player) -> None:
        if player not in self.players:
            print(f"Can't remove player {player.name} from {self.name}. They were not selected to be part of it")
            return
        self.players.remove(player)

    def remaining_slots(self) -> int:
        return self.capacity - len(self.players)


def window(seq: List, n: int = 2) -> Iterator:
    return iter(seq[i: i + n] for i in range(len(seq) - n + 1))


class Constraint:
    TWO_SAME_DAY = 0
    NIGHT_THEN_MORNING = 1
    TWO_CONSECUTIVE_DAYS = 2
    THREE_CONSECUTIVE_DAYS = 3
    MORE_CONSECUTIVE_DAYS = 4

    NAMES = {
        "Jouer deux jeux dans la même journée": TWO_SAME_DAY,
        "Jouer un soir et le lendemain matin": NIGHT_THEN_MORNING,
        "Jouer deux jours consécutifs": TWO_CONSECUTIVE_DAYS,
        "Jouer trois jours consécutifs": THREE_CONSECUTIVE_DAYS,
        "Jouer plus de trois jours consécutifs": MORE_CONSECUTIVE_DAYS
    }


class Player:
    ACTIVE_PLAYERS = 0

    def __init__(self, name: str,
                 wishes: List[Activity],
                 non_availabilities: List[TimeSlot],
                 max_activities: Optional[int] = None,
                 blacklist: Optional[List[Player]] = None,
                 constraints: Optional[Set[Constraint]] = None):
        # Auto number the players
        self.id = Player.ACTIVE_PLAYERS
        Player.ACTIVE_PLAYERS += 1

        self.name = name
        self.wishes = wishes
        self.non_availability: List[TimeSlot] = non_availabilities
        self.max_activities = max_activities
        self.blacklist: List[Player] = blacklist if blacklist is not None else []
        self.constraints: Set[Constraint] = constraints if constraints is not None else set()

        self.activities: List[Activity] = []

        self.filter_availability(verbose=True)
        self.update_wishlist(verbose=True)

    def filter_availability(self, verbose:bool = False) -> None:
        conflicting = [a for a in self.wishes for slot in self.non_availability if a.overlaps(slot.start, slot.end)]
        if verbose and conflicting:
            print("Found wishes where not available :")
            for a in set(conflicting):
                print(f"- {a}")

        for a in set(conflicting):
            self.wishes.remove(a)

    def update_wishlist(self, verbose:bool = False) -> None:
        impossible_activities = []
        for activity in self.activities:
            impossible_activities.extend([a for a in self.wishes if a.conflicts_with(activity, self)])

        if verbose and impossible_activities:
            print("Found impossible wishes :")
            for a in set(impossible_activities):
                print(f"- {a}")

        for a in set(impossible_activities):
            self.wishes.remove(a)

    def __repr__(self):
        return f"{self.id} | {self.name}"

    def could_play(self, activity: Activity) -> bool:
        if self.name == "Arnaud Oliveau":
            print("Arnaud")
        if (self.max_activities is not None) and (len(self.activities) >= self.max_activities):
            return False

        return not(any(activity.overlaps(ts.start, ts.end) for ts in self.non_availability)
                   or any(activity.conflicts_with(a, self) for a in self.activities))

    def remove_wish(self, activity: Activity) -> None:
        self.wishes = [a for a in self.wishes if a != activity]

    def has_wishes(self) -> bool:
        return len(self.wishes) > 0

    def add_activity(self, activity: Activity) -> None:
        self.activities.append(activity)
        self.remove_wish(activity)

        # remove conflicting wishes
        self.update_wishlist()
        # Remove activities with the same name
        self.wishes = [a for a in self.wishes if a.name != activity.name]

        # If we reached the max number of activities, empty the wishlist
        if self.max_activities is not None and len(self.activities) >= self.max_activities:
            self.wishes = []

    def remove_activity(self, activity: Activity) -> None:
        if activity not in self.activities:
            print(f"Can't remove activity {activity.name} from {self.name}. They were not selected to be part of it")
            return
        self.activities.remove(activity)

    def add_blacklist_player(self, player: Player) -> None:
        self.blacklist.append(player)

    def is_last_chance(self):
        """If the player has not been cast yet and only one wish remains"""
        return (len(self.activities) == 0) and (len(self.wishes) == 1)

    def activity_rank(self, activity: Activity) -> int:
        return self.wishes.index(activity)

    def possible_wishes(self) -> List[Activity]:
        # Remove activities that are full
        w = [a for a in self.wishes if not a.is_full()]
        # remove activities with bl conflict
        # Remove activities where there is a target already casted
        for player_bl in self.blacklist:
            w = [a for a in w if player_bl not in a.players]

        # Remove activities where someone in the cast blacklisted us
        w = [a for a in w if not any([self in p.blacklist for p in a.players])]

        return w


class Matching:
    def __init__(self, players: List[Player], activities: List[Activity]):
        self.active_players = players
        self.active_activities = activities

        self.done_players: List[Player] = []
        self.done_activities: List[Activity] = []

    def find_activity(self, id: int) -> Activity:
        return [a for a in self.active_activities + self.done_activities if a.id == id][0]

    def find_activity_by_name(self, name: str) -> List[Activity]:
        act = [a for a in self.active_activities + self.done_activities if a.name.lower() == name.lower()]
        if not act:
            raise ValueError(f"ERROR. Found no activity with name {name}")
        return act

    def find_player(self, id: int) -> Player:
        return [p for p in self.active_players + self.done_players if p.id == id][0]

    def find_player_by_name(self, name: str) -> Player:
        pl = [p for p in self.active_players + self.done_players if p.name.lower() == name.lower()]
        if not pl:
            raise ValueError(f"ERROR. Found no players with name {name}")
        return pl[0]

    def cleanup(self) -> None:
        while True:
            # Find activities that are full
            full_activities = [a for a in self.active_activities if a.is_full()]
            # Remove them from the active list
            for a in full_activities:
                self.active_activities.remove(a)
                self.done_activities.append(a)

            # If a player has no more possible wishes, remove it
            new_inactive_players = [p for p in self.active_players if not p.has_wishes()]
            for p in new_inactive_players:
                self.done_players.append(p)
                self.active_players.remove(p)

            # If we modified some things, restart the cleanup procedure
            # Else, break out of the loop and return
            if not full_activities and not new_inactive_players:
                return

    def assign_activity(self, player: Player, activity: Activity) -> None:
        # First check if activity has room left
        if activity.is_full():
            print(f"Tried to give [{activity.name}] to {player.name} but it is full.")
            return

        # Check potential blacklist conflicts with other players
        # Check if someone in player's blacklist is already in the cast
        for p in player.blacklist:
            if p in activity.players:
                print(f"Could not give {activity.name} to {player.name} because of some blacklist conflict")
                return

        # Check if someone in the cast blacklisted player
        for p in activity.players:
            if player in p.blacklist:
                print(f"Could not give {activity.name} to {player.name} because of some blacklist conflict")
                return

        # Add the activity to the player cast list, and the player to the activity cast list
        print(f"Giving [{activity.name}] to {player.name}")
        player.add_activity(activity)
        activity.add_player(player)

        # Then, cleanup full activities or players with no more wishes
        self.cleanup()

    def _remove_from_activity(self, player: Player, activity: Activity) -> None:
        print(f"Removing {player.name} from the activity {activity.name}")
        player.remove_activity(activity)
        activity.remove_player(player)
        # The activity may now have available slots. So update it !
        if activity not in self.active_activities:
            self.done_activities.remove(activity)
            self.active_activities.append(activity)

    def remove_from_activity(self, player_name: str, activity_name: str) -> None:
        act = self.find_activity_by_name(activity_name)
        if len(act) != 1:
            print(f"Multiple activities have the name {activity_name}. Could not make the difference.")
            print("Instead, use `remove_from_activity_by_id(player, id)` with the unique activity ID")
            print(f"Activities that matched : ")
            for a in act:
                print(a)
            return
        self._remove_from_activity(self.find_player_by_name(player_name), act[0])

    def remove_from_activity_by_id(self, player_name: str, activity_id: int) -> None:
        self._remove_from_activity(self.find_player_by_name(player_name), self.find_activity(activity_id))

    def force_assign_activity(self, player_name: str, activity_name: str) -> None:
        act = self.find_activity_by_name(activity_name)
        if len(act) != 1:
            print(f"Multiple activities have the name {activity_name}. Could not make the difference.")
            print("Instead, use `force_assign_activity_by_id(player, id)` with the unique activity ID")
            print(f"Activities that matched : ")
            for a in act:
                print(a)
            return

        self.assign_activity(self.find_player_by_name(player_name), act[0])

    def force_assign_activity_by_id(self, player_name: str, activity_id: int) -> None:
        self.assign_activity(self.find_player_by_name(player_name), self.find_activity(activity_id))

    def add_to_blacklist(self, playerA_name: str, playerB_name: str) -> None:
        pA = self.find_player_by_name(playerA_name)
        pB = self.find_player_by_name(playerB_name)
        pA.add_blacklist_player(pB)
        pB.add_blacklist_player(pA)

    def cast_if_one_wish(self) -> bool:
        """For each player that has no activity yet and only one possible remaining wish, try to give it to them.
        Return True if we found such players and gave things to them. Else, return False"""

        targets = [p for p in self.active_players if p.is_last_chance()]
        if len(targets) == 0:
            return False

        print(f"I found {len(targets)} players with one last chance to get a cast")
        # Shuffle the list, because we may not be able to give all wishes
        random.shuffle(targets)
        for player in targets:
            activity = player.wishes[0]
            self.assign_activity(player, activity)

        return True

    def prepare_hospital_resident_dictionaries(self) -> Tuple[Dict, Dict, Dict]:
        player_wishes: Dict[Player, List[Activity]] = {p: p.possible_wishes()
                                                       for p in self.active_players}

        capacities = {a: a.remaining_slots() for a in self.active_activities}

        activities_waiting_list: Dict[Activity, List[Player]] = {
            a: self.generate_activity_waiting_list(player_wishes, a)
            for a in self.active_activities}

        # removing activities that no one wished
        unwanted = [a for (a, w) in activities_waiting_list.items() if len(w) == 0]
        for a in unwanted:
            activities_waiting_list.pop(a)
            capacities.pop(a)

        # removing players with no wishes
        finished = [p for (p, w) in player_wishes.items() if w == []]
        for p in finished:
            player_wishes.pop(p)
            for (a, wl) in activities_waiting_list.items():
                if p in wl:
                    wl.remove(p)

        return player_wishes, activities_waiting_list, capacities

    def generate_activity_waiting_list(self, player_wishes: Dict[Player, List[Activity]],
                                       activity: Activity) -> List[Player]:
        # Get the players that wanted this activity
        interested_players: List[Player] = [p for (p, wishes) in player_wishes.items() if activity in wishes]
        # Shuffle them
        random.shuffle(interested_players)
        # Then, sort by the number of activities that a given player already has and then
        # the rank of the activity on the wishlist of each player, so that a wish
        # in first position is stronger than a wish in 10th position, but a player with 2 activities has priority over
        # someone with 5
        interested_players.sort(key=lambda p: (len(p.activities), p.activity_rank(activity)))
        return interested_players

    def cast_with_hospital_residents(self) -> bool:
        """Returns True if the function did cast som players. False if nothing was done"""
        player_wishes, activities_waiting_list, capacities = self.prepare_hospital_resident_dictionaries()

        game = HospitalResident.create_from_dictionaries(player_wishes, activities_waiting_list, capacities)
        match = game.solve(optimal="resident")

        # Match returns a Dict[Hospital, List[Resident]]
        # So to access the Activity and Player underneath, we must use the .name method
        # The objects are cloned, so we have to find the activity back with its ID
        did_something = False
        for (a, cast) in match.items():
            for p in cast:
                activity = self.find_activity(a.name.id)
                player = self.find_player(p.name.id)
                self.assign_activity(player, activity)
                did_something = True
        return did_something

    def print_activities_status(self) -> None:
        print("Activities with a full cast:")
        for a in self.done_activities:
            print(f"* {a}")
            for p in a.players:
                print(f"  - {p.name}")
            print("")

        print("Activities WITHOUT a full cast:")
        for a in self.active_activities:
            print(f"* {a}")
            for p in a.players:
                print(f"  - {p.name}")
            print(f" Missing {a.remaining_slots()} more")
            print("")

    def print_players_status(self) -> None:
        print("Activities given to each player:")
        for p in self.active_players + self.done_players:
            print(f"* {p.name} | Got {len(p.activities)} activities. Max {p.max_activities}")
            for a in p.activities:
                print(f"  - {a.name} | Start: {a.start}")

    def solve(self) -> None:
        while True:
            print("Casting in priority the players with only one wish and no casts yet")
            while self.cast_if_one_wish():
                self.cleanup()

            print("No more priority players. Now casting like usual")
            if not self.cast_with_hospital_residents():
                break
            self.cleanup()
        print("Done")

    def print_available_players(self) -> None:
        slots = generate_all_timeslots()
        for s in slots:
            dummy_activity = Activity(f"{s}", 1000, s.start, s.end)
            potential_players = [p for p in self.active_players + self.done_players
                                 if p.could_play(dummy_activity)]
            print(f"{s},{','.join([p.name for p in potential_players])}")
