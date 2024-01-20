# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
from colors import *
from commands.typed import TypedSayCommand, TypedClientCommand
from events import Event
from engines.server import engine_server
from engines.server import global_vars
from entities.helpers import index_from_edict
from listeners.tick import GameThread
from players.helpers import index_from_userid
from filters.players import PlayerIter, Player
from messages.hooks import HookUserMessage
from messages import SayText2
from listeners.tick import Delay
import paths
from listeners import OnConVarChanged
from listeners import OnPlayerRunCommand
from listeners import OnPlayerPostRunCommand

# Core Imports
import os
import threading
import json
import socket
import requests

# 3rd party imports
import requests
import pymysql
import vdf

MAP_CHECK_LOCK = threading.Lock()

def load():
    SayText2('NextMap plugin has been loaded successfully!').send()

def unload():
    SayText2('NextMap plugin has been unloaded successfully!').send()

# =============================================================================
# >> Utils
# =============================================================================
def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = GameThread(target=fn, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
    return wrapper

#this works
@OnConVarChanged
def on_convar_changed(convar, old_value):
    check_map_list(convar)

@threaded
def check_map_list(map_name):
    global MAP_CHECK_LOCK
      
    with MAP_CHECK_LOCK:
        player_count = len([player for player in PlayerIter('human')])
        server_hostname = socket.gethostname()
        #check if map is pending
        #get discord ID
        #say map is next
        map_data = get_pending_map_data(map_name)
        if map_data:
            discord_user_id = map_data['discord_user_id']
            send_discord_message(map_name, player_count, discord_user_id, f"https://bot.tf2maps.net/connect/?server={server_hostname}:27015")

def send_discord_message(map_name, player_count, discord_user_id, server_url):
    filepath = os.path.join(paths.GAME_PATH, "addons/source-python/plugins/pingdiscord/config.json")

    with open(filepath) as file:
        config = json.load(file)

    data = {
        "content" : f"<@{discord_user_id}> {map_name} is set as the **next map** on {server_url} with {player_count} players.",
        "username" : "Mecha Engineer"
    }            
    result = requests.post(config['webhook_url'], json=data)
    result.raise_for_status()

def get_pending_map_data(map_name):
    connection = get_db_connection()

    with connection.cursor() as cursor:
        query = (
            "SELECT * "
            "FROM maps "
            "WHERE map=(%s) AND status='pending' LIMIT 1 "
        )
        cursor.execute(query, (map_name))
        result = cursor.fetchone()

    return result

def get_db_connection():
    filepath = os.path.join(paths.GAME_PATH, "addons/sourcemod/configs/databases.cfg")

    with open(filepath) as file:
        databases = vdf.load(file)

    database = databases['Databases']['maplist']

    connection = pymysql.connect(
        host=database['host'],
        user=database['user'],
        port=int(database['port']),
        password=database['pass'],
        database=database['database'],
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection