# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
from colors import *
from commands.typed import TypedSayCommand, TypedClientCommand
from events import Event
from engines.server import engine_server
from entities.helpers import index_from_edict
from listeners.tick import GameThread
from players.helpers import index_from_userid
from filters.players import PlayerIter, Player
from messages.hooks import HookUserMessage
from messages import SayText2
from listeners.tick import Delay
import paths

# Core Imports
import random
import os

# 3rd Party Imports
import vdf
import pymysql


# =============================================================================
# >> GLOBAL VARS
# =============================================================================
USERS = {}
XF_RANKS = {
    19: "VIP",
    36: "Server Mod",
    38: "Gold Star",
    39: "Comp Host",
    3: "Senior Staff",
    4: "Staff"
}
RANK_PREFIXES = {
    "VIP": f"{DARK_GREEN}VIP",
    "Server Mod": f"{CYAN}Server Mod",
    "Gold Star": f"{YELLOW}Gold Star",
    "Comp Host": f"{YELLOW}Comp Host",
    "Senior Staff": f"{PURPLE}Senior Staff",
    "Staff": f"{RED}Staff"
}

# =============================================================================
# >> FILTERS
# =============================================================================
def player_filter(value):
    value = str(value).lower()

    if value in ["all", "bot", "human", "bot", "alive", "dead"]:
        yield from PlayerIter(value)
    elif value == "blu":
        yield from PlayerIter("ct")
    elif value == "red":
        yield from PlayerIter("t")
    elif value == "spec":
        yield from PlayerIter("spec")
        yield from PlayerIter("un")
    else:
        for player in PlayerIter():
            if player.name.lower().startswith(value):
                yield player
                break
        else:
            raise Exception

# =============================================================================
# >> COMMANDS
# =============================================================================
@TypedSayCommand("!spec", permission="admin.move_players")
@TypedClientCommand("sp_spec", permission="admin.move_players")
def on_move_to_spec(command_info, players:player_filter):
    for player in players:
        player.set_team(1)

@TypedSayCommand("!blu", permission="admin.move_players")
@TypedClientCommand("sp_blu", permission="admin.move_players")
def on_move_to_blu(command_info, players:player_filter):
    for player in players:
        player.set_team(3)

@TypedSayCommand("!red", permission="admin.move_players")
@TypedClientCommand("sp_red", permission="admin.move_players")
def on_move_to_red(command_info, players:player_filter):
    for player in players:
        player.set_team(2)

@TypedSayCommand("!ban", permission="admin.kick")
@TypedClientCommand("sp_ban", permission="admin.kick")
def on_ban(command_info, players:player_filter):
    kicker = Player(command_info.index)
    for player in players:
        player.ban()

@TypedSayCommand("!kick", permission="admin.kick")
@TypedClientCommand("sp_kick", permission="admin.kick")
def on_kick(command_info, players:player_filter):
    kicker = Player(command_info.index)
    for player in players:
        player.kick(f"You were kicked by {kicker.name}")

@TypedSayCommand("!mute", permission="admin.mute")
@TypedClientCommand("sp_mute", permission="admin.mute")
def on_mute(command_info, players:player_filter):
    for player in players:
        player.mute()

@TypedSayCommand("!unmute", permission="admin.mute")
@TypedClientCommand("sp_unmute", permission="admin.mute")
def on_unmute(command_info, players:player_filter):
    for player in players:
        player.unmute()

@TypedSayCommand("!slay", permission="admin.slay")
@TypedClientCommand("sp_slay", permission="admin.slay")
def on_kys(command_info, players:player_filter):
    for player in players:
        if player.team in [2,3]:
            player.play_sound(f"player/shove{random.randint(1,10)}.wav")
            player.slay()

@TypedSayCommand("!name", permission="admin.rename")
@TypedClientCommand("sp_name", permission="admin.rename")
def on_name(command_info, players:player_filter, new_name:str):
    for player in players:
        player.set_name(new_name)

@TypedSayCommand("!noclip", permission="admin.noclip")
@TypedClientCommand("sp_noclip", permission="admin.noclip")
def on_noclip(command_info, players:player_filter):
    for player in players:
        player.set_noclip(not player.noclip)

@TypedSayCommand("!steamid", permission="admin.info")
@TypedClientCommand("sp_steamid", permission="admin.info")
def on_steamid(command_info, players:player_filter):
    for player in players:
        command_info.reply(f"{WHITE}Name: {ORANGE}{player.name}{WHITE}, STEAM_ID: {ORANGE}{player.steamid}")

@TypedSayCommand("!rup", permission="admin.rup")
@TypedClientCommand("rup", permission="admin.rup")
def on_rup(command_info):
    teams = {"RED":2, "BLU": 3}
    for team_name, team_id in teams.items():
        fake_client = engine_server.create_fake_client(f'RUP BOT {team_name}')
        fake_player = Player(index_from_edict(fake_client))
        fake_player.team = team_id
        fake_player.client_command("tournament_readystate 1", True)
        fake_player.kick()

# =============================================================================
# >> EVENTS
# =============================================================================
@Event("player_activate")
def on_player_activate(event):
    args = event.variables.as_dict()

    index = index_from_userid(args['userid'])
    player = Player(index)

    if player.is_player():
        assign_permissions(player)

@HookUserMessage('SayText2')
def _saytext2_hook(recipients, data):
    global USERS
    global RANK_PREFIXES
    key = data.message

    # Is this message from a player sending chat?
    if key not in ["TF_Chat_All", "TF_Chat_Team", "TF_Chat_Dead", "TF_Chat_AllDead", "TF_Chat_AllSpec", "TF_Chat_Spec"]:
        return

    player = Player(data.index)

    # Check if player has a rank in global vars
    rank = USERS.get(player.steamid)
    if not rank:
        return
    
    prefix = ""

    if key in ["TF_Chat_Dead", "TF_Chat_AllDead"]:
        prefix += "*DEAD* "
    if key in ["TF_Chat_Team"]:
        prefix += "(TEAM) "
    prefix += f"{WHITE}[{RANK_PREFIXES[rank]}{WHITE}] "

    tokens = {'data': data, 'prefix': prefix}

    # Use a delay to avoid crashing the server
    Delay(0, _send_new_message, (key, data.index, list(recipients)), tokens)

    # Remove all recipients for the current message to block it
    recipients.remove_all_players()

def _send_new_message(key, index, *ply_indexes, **tokens):
    message = SayText2(
        message="{prefix} \x03{data.param1}\x01: {data.param2}",
        index=index,
    )
    message.send(*ply_indexes, **tokens)


# =============================================================================
# >> UTILS
# =============================================================================
def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = GameThread(target=fn, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
    return wrapper

@threaded
def assign_permissions(player):
    global USERS
    global XF_RANKS

    steamid_64 = int(player.steamid.split(":")[2].replace("]", "")) + 76561197960265728
    xf_user = lookup_xf_user(steamid_64)

    if not xf_user:
        return

    secondary_groups = [int(gid) for gid in xf_user['secondary_group_ids'].decode('utf-8').split(",")]

    if xf_user['user_group_id'] == 2:
        if 19 in secondary_groups:
            USERS[player.steamid] = XF_RANKS[19]
        elif 39 in secondary_groups:
            USERS[player.steamid] = XF_RANKS[39]
            player.permissions.add("*.*")
            print(f"SP Admin: Granting *.* permissions to {player.name}")

    if xf_user['user_group_id'] in [39, 36, 38, 3, 4]:
        player.permissions.add('*.*')
        print(f"SP Admin: Granting *.* permissions to {player.name}")

def lookup_xf_user(steam_id64):
    filepath = os.path.join(paths.GAME_PATH, "addons/sourcemod/configs/databases.cfg")

    with open(filepath) as file:
        databases = vdf.load(file)

    database = databases['Databases']['xenforo']

    connection = pymysql.connect(
        host=database['host'],
        user=database['user'],
        port=int(database['port']),
        password=database['pass'],
        database=database['database'],
        cursorclass=pymysql.cursors.DictCursor
    )

    with connection.cursor() as cursor:
        query = (
            "SELECT xf_user.user_id, xf_user.username, xf_user.user_group_id, xf_user.secondary_group_ids "
            "FROM xf_user INNER JOIN xf_user_external_auth ON xf_user.user_id=xf_user_external_auth.user_id "
            "WHERE provider='steam' AND provider_key=(%s) LIMIT 1"
        )

        cursor.execute(query, (steam_id64))
        result = cursor.fetchone()

        return result
