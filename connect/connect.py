# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
from events.hooks import PreEvent
from events.hooks import EventAction
from players.entity import Player
from filters.players import PlayerIter
from messages.hooks import HookUserMessage
from messages import SayText2
from colors import GRAY, LIGHT_GRAY, WHITE, ORANGE, Color

# Core Imports
import random

# =============================================================================
# >> UTILITY FUNCTIONS
# =============================================================================
def announce(message):
    print(message)
    for player in PlayerIter("human"):
        SayText2(message).send(player.index)

# =============================================================================
# >> EVENT LISTENERS
# =============================================================================
@PreEvent('player_connect', 'player_connect_client')
def on_connect(event):
    args = event.variables.as_dict()

    if bool(args['bot']):
        return EventAction.STOP_BROADCAST

    if event.name == "player_connect":
        announce(f"{ORANGE}{args['name']} {WHITE}joined the server.")

    return EventAction.STOP_BROADCAST

@PreEvent('player_disconnect')
def on_disconnect(event):
    args = event.variables.as_dict()

    if bool(args['bot']):
        return EventAction.STOP_BROADCAST

    if args['reason']:
        announce(f"{ORANGE}{args['name']} {WHITE}left the server. {ORANGE}Reason: {WHITE}{args['reason']}")
    else:
        announce(f"{ORANGE}{args['name']} {WHITE}disconnected!")

    return EventAction.STOP_BROADCAST

@PreEvent('player_team')
def on_jointeam(event):
    args = event.variables.as_dict()

    player = Player.from_userid(args['userid'])

    if player.is_bot:
        return EventAction.STOP_BROADCAST

    new_team = args['team']
    old_team = args['oldteam']
    disconnect = bool(args['disconnect'])

    RED_TEAM = Color(226,58,29)
    BLUE_TEAM = Color(154,205,255)
    team_names = ['UNASSIGNED', 'SPECTATORS', 'RED', 'BLU']
    team_colors = [f"{LIGHT_GRAY}", f"{LIGHT_GRAY}", f"{RED_TEAM}", f"{BLUE_TEAM}"]

    if not disconnect:
        verb = "joined team"
        if old_team == 2 or old_team == 3:
            verb = "switched teams to"

        announce(f"{team_colors[old_team]}{player.name}{WHITE} {verb} {team_colors[new_team]}{team_names[new_team]}{WHITE}!")

    return EventAction.STOP_BROADCAST