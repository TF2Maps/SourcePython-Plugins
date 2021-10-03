# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
from listeners import OnLevelInit 
from listeners.tick import GameThread
from engines.server import global_vars
from filters.players import PlayerIter
from events import Event
import paths

# Core Imports
import os
import threading
import json
import socket

# 3rd party imports
import requests
import pymysql
import vdf

MAP_CHECK_LOCK = threading.Lock()


# =============================================================================
# >> Events
# =============================================================================
@Event('player_connect')
def on_player_connect(event):
    check_map()


# =============================================================================
# >> Utils
# =============================================================================
def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = GameThread(target=fn, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
    return wrapper


@threaded
def check_map():
    global MAP_CHECK_LOCK
      
    with MAP_CHECK_LOCK:
        player_count = len([player for player in PlayerIter('human')])
        map_name = global_vars.map_name
        server_hostname = socket.gethostname()

        if player_count >= 10:
            map_data = get_pending_map_data(map_name)
                
            if map_data:
                discord_user_id = map_data['discord_user_id']
                remove_map_from_queue(map_name)
                send_discord_message(map_name, player_count, discord_user_id, f"steam://connect/{server_hostname}:27015")
    

def send_discord_message(map_name, player_count, discord_user_id, server_url):
    filepath = os.path.join(paths.GAME_PATH, "addons/source-python/plugins/pingdiscord/config.json")

    with open(filepath) as file:
        config = json.load(file)

    data = {
        "content" : f"<@{discord_user_id}> {map_name} is currently being played on {server_url} with {player_count} players.",
        "username" : "Nesman-Dev"
    }            
    result = requests.post(config['webhook_url'], json=data)
    result.raise_for_status()


def remove_map_from_queue(map_name):
    connection = get_db_connection()

    with connection.cursor() as cursor:
        query = (
            "UPDATE maps "
            "SET status='played' "
            "WHERE map=(%s) and status='pending' "
        )
        cursor.execute(query, (map_name))
        connection.commit()


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