# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
from commands.typed import TypedSayCommand, TypedClientCommand
from events import Event
from engines.server import engine_server
from entities.helpers import index_from_edict
from listeners.tick import GameThread
from players.helpers import index_from_userid
from filters.players import PlayerIter, Player

from colors import ORANGE, WHITE
import paths

# Core Imports
import random
import os

# 3rd Party Imports
import vdf

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

    assign_permissions(player)

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
    steamid_64 = int(player.steamid.split(":")[2].replace("]", "")) + 76561197960265728
    xf_user = lookup_xf_user(steamid_64)

    if xf_user['user_group_id'] in [36, 38, 3, 4]:
        player.permissions.add('*.*')
        print(f"granting permissions to {player}")

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
