# =============================================================================
# >> IMPORTS
# =============================================================================

# Source.Python Imports
from filters.players import Player
import paths
from events import Event
from players.helpers import playerinfo_from_userid, index_from_playerinfo

# Core Imports
import time
import os
import json
from datetime import datetime


LOG_FILE=os.path.join(paths.GAME_PATH, f"logs/chat/{datetime.now().strftime('%Y-%m-%d')}.log")
LOG_FILE_HANDLE=None
   

def load():
    global LOG_FILE_HANDLE
    global LOG_FILE

    LOG_FILE_HANDLE = open(LOG_FILE, "a")

def unload():
    global LOG_FILE_HANDLE
    LOG_FILE_HANDLE.close()


@Event("player_say")
def on_player_say(event):
    global LOG_FILE_HANDLE

    player_info = playerinfo_from_userid(event['userid'])
    player_index = index_from_playerinfo(player_info)
    player = Player(player_index)

    try:
        rank = player.rank
    except AttributeError: 
        rank = None

    log_message = {
        "timestamp:": int(time.time()), 
        "rank": rank, 
        "steam_id": player.steamid, 
        "user_name": player.name, 
        "message": event['text']
    }

    LOG_FILE_HANDLE.write(f"{json.dumps(log_message)}\n")
    LOG_FILE_HANDLE.flush()



