from __future__ import annotations

from typing import List, Dict, Optional
from matching.games import HospitalResident
import random
import datetime


class Activity:
    ACTIVE_ACTIVITIES = 0

    def __init__(self, name: str, capacity: int, start: datetime.datetime, end: datetime.datetime):
        # Auto number the activities
        self.id = Activity.ACTIVE_ACTIVITIES
        Activity.ACTIVE_ACTIVITIES += 1

        self.name = name
        self.capacity = capacity
        self.start = start
        self.end = end

        self.players: List[Player] = []

    def __repr__(self):
        return f"{self.id} | {self.name} | {len(self.players)} / {self.capacity} players | {self.start} - {self.end}"

    def conflicts_with(self, other: Activity) -> bool:
        if (self.start <= other.start) and (other.start < self.end):
            return True
        elif (other.start <= self.start) and (self.start < other.end):
            return True
        else:
            return False

    def find_conflicting_activities(self, activities: List[Activity]) -> List[Activity]:
        return [a for a in activities if self.conflicts_with(a)]

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


class Player:
    ACTIVE_PLAYERS = 0

    def __init__(self, name: str,
                 wishes: List[Activity],
                 max_activities: Optional[int] = None,
                 blacklist: Optional[List[Player]] = None):
        # Auto number the players
        self.id = Player.ACTIVE_PLAYERS
        Player.ACTIVE_PLAYERS += 1

        self.name = name
        self.wishes = wishes
        self.max_activities = max_activities
        self.blacklist: List[Player] = blacklist if blacklist is not None else []

        self.activities: List[Activity] = []

    def __repr__(self):
        return f"{self.id} | {self.name}"

    def remove_wish(self, activity: Activity) -> None:
        self.wishes = [a for a in self.wishes if a != activity]

    def has_wishes(self) -> bool:
        return len(self.wishes) > 0

    def add_activity(self, activity: Activity) -> None:
        self.activities.append(activity)
        self.remove_wish(activity)
        # remove conflicting wishes
        self.wishes = [a for a in self.wishes if not activity.conflicts_with(a)]
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


class Matching:
    def __init__(self, players: List[Player], activities: List[Activity]):
        self.active_players = players
        self.active_activities = activities

        self.done_players: List[Player] = []
        self.done_activities: List[Activity] = []

    def find_activity(self, id: int) -> Activity:
        return [a for a in self.active_activities + self.done_activities if a.id == id][0]

    def find_activity_by_name(self, name: str) -> Activity:
        return [a for a in self.active_activities + self.done_activities if a.name == name][0]

    def find_player(self, id: int) -> Player:
        return [p for p in self.active_players + self.done_players if p.id == id][0]

    def find_player_by_name(self, name: str) -> Player:
        return [p for p in self.active_players + self.done_players if p.name == name][0]

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

        # Check potential blacklist conflicts from the same wave
        for p in player.blacklist:
            if p in activity.players:
                print(f"Could not give {activity.name} to {player.name} because of some blacklist conflict")
                return

        # Add the activity to the player cast list, and the player to the activity cast list
        print(f"Giving [{activity.name}] to {player.name}")
        player.add_activity(activity)
        activity.add_player(player)
        # Checking the player's blacklist and remove all players from being cast to this activity
        for p in player.blacklist:
            p.remove_wish(activity)
        # Check the other players blacklists
        for p in self.active_players:
            if player in p.blacklist:
                p.remove_wish(activity)

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
        self._remove_from_activity(self.find_player_by_name(player_name), self.find_activity_by_name(activity_name))

    def force_assign_activity(self, player_name: str, activity_name:str) -> None:
        self.assign_activity(self.find_player_by_name(player_name), self.find_activity_by_name(activity_name))

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

    def generate_activity_waiting_list(self, activity: Activity) -> List[Player]:
        # Get the players that wanted this activity
        interested_players: List[Player] = [p for p in self.active_players if activity in p.wishes]
        # Shuffle them
        random.shuffle(interested_players)
        # Then, sort by the rank of the activity on the wishlist of each player, so that a wish
        # in first position is stronger than a wish in 10th position
        interested_players.sort(key=lambda p: p.activity_rank(activity))
        return interested_players

    def remove_impossible_wishes(self, wishes: List[Activity]) -> List[Activity]:
        return [a for a in wishes if not a.is_full()]

    def cast_with_hospital_residents(self) -> bool:
        """Returns True if the function did cast som players. False if nothing was done"""
        player_wishes: Dict[Player, List[Activity]] = {p: self.remove_impossible_wishes(p.wishes)
                                                       for p in self.active_players}
        activities_waiting_list: Dict[Activity, List[Player]] = {a: self.generate_activity_waiting_list(a)
                                                                 for a in self.active_activities}
        capacities = {a: a.remaining_slots() for a in self.active_activities}


        # removing activities that no one wished
        unwanted = [a for (a, w) in activities_waiting_list.items() if len(w) == 0]
        for a in unwanted:
            activities_waiting_list.pop(a)
            capacities.pop(a)

        # removing players with no wishes
        finished = [p for (p, w) in player_wishes.items() if w == []]
        for p in finished:
            player_wishes.pop(p)

        game = HospitalResident.create_from_dictionaries(player_wishes, activities_waiting_list, capacities)
        match = game.solve(optimal="resident")

        # Match returns a Dict[Hospital, List[Resident]]
        # So to access the Activity and Player underneath, we must use the .name method
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
            for _ in range(len(a.players), a.capacity):
                print(f"  - ")
            print("")

    def print_players_status(self) -> None:
        print("Activities given to each player:")
        for p in self.active_players + self.done_players:
            print(f"* {p.name} | Got {len(p.activities)} activities")
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
