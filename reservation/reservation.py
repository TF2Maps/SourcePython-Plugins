# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
from colors import ORANGE, WHITE
from commands.typed import TypedSayCommand, TypedServerCommand, TypedClientCommand
from messages import SayText2
from engines.server import execute_server_command
from listeners.tick import Delay
from filters.players import PlayerIter

# Core Imports
import time
import json

# =============================================================================
# >> COMMANDS
# =============================================================================
@TypedSayCommand("!extend", permission="reservation.extend")
@TypedClientCommand("sp_extend", permission="reservation.extend")
def on_extend(command_info):
    if get_remaining_time() > 30*60:
        remaining = readable_time(get_remaining_time())
        SayText2(f"Reservation can only be extended with <{ORANGE}30 {WHITE}minutes remaining. Time remaining: {ORANGE}{remaining}").send()
        return
    else:
        extend_time(60)
        remaining = readable_time(get_remaining_time())
        alert(f"Reservation been extended by {ORANGE}1 hour{WHITE}. Time remaining: {ORANGE}{remaining}")

@TypedSayCommand("!time", permission="reservation.time")
@TypedClientCommand("sp_time", permission="reservation.time")
def on_time(command_info):
    remaining = readable_time(get_remaining_time())
    SayText2(f"Time remaining: {ORANGE}{remaining}").send()

@TypedSayCommand("!shutdown", permission="reservation.shutdown")
@TypedClientCommand("sp_shutdown", permission="reservation.shutdown")
def on_shutdown(command_info):
    alert(f"Server scheduled for shutdown by admin request")
    Delay(5, lambda: shutdown())

@TypedSayCommand("!restart", permission="reservation.restart")
@TypedClientCommand("sp_restart", permission="reservation.restart")
def on_restart(command_info):
    alert(f"Server will restart in {ORANGE}10 {WHITE}seconds by admin request")
    Delay(10, lambda: execute_server_command("_restart"))

@TypedServerCommand("shutdown_alert")
def on_shutdown_alert(command_info, minutes: int):
    alert(f"System will automatically shutdown in {ORANGE}{minutes} {WHITE}minutes. Type {ORANGE}!extend {WHITE}to add time!")

@TypedServerCommand("alert")
def on_alert(command_info, message: str):
    alert(message)

# =============================================================================
# >> UTILITY FUNCTIONS
# =============================================================================
def extend_time(minutes):
    """
        Extends the time the server will run for
    """
    old = int(get_attribute("ttl"))
    new = int(old + minutes)

    set_attribute("ttl", new)

def shutdown():
    """
        Schedules the server for shutdown by setting the TTL to 0
    """
    set_attribute("ttl", 0)

    for player in PlayerIter('human'):
        player.kick("Reservation ended. Thanks for playing!")

def get_attribute(name):
    """
        Get an attribute from the tags file
        Tags are variables passed into the machine at boot time and rendered into this file
    """
    with open("/opt/tags.json") as file:
        tags = json.load(file)
        return tags.get(name)

def set_attribute(name, value):
    """
        Set an attribute in the tags file
    """
    with open("/opt/tags.json") as file:
        tags = json.load(file)

    tags[name] = value

    with open("/opt/tags.json", "w") as file:
        json.dump(tags, file)

def get_remaining_time():
    """
        Compares the boot time to the TTL
        Returns number of seconds left on the reservation
    """
    ttl = int(get_attribute("ttl"))
    launch_time = int(get_attribute("launch_time"))

    ttl = ttl * 60
    elapsed = time.time() - launch_time
    remaining = ttl - elapsed if ttl > elapsed else 0

    return remaining

def readable_time(seconds, granularity=6):
    """
        Takes seconds and outputs a pretty human readable time
        Copied from: https://stackoverflow.com/a/24542445/4625857
    """
    if seconds <= 0:
        return "None"

    intervals = (
        ('years', 60*60*24*30*12),
        ('months', 60*60*24*30),
        ('weeks', 60*60*24*7),
        ('days', 60*60*24),
        ('hours', 60*60),
        ('minutes', 60),
    )
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            value = int(value)
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append(f"{value} {name}")
        else:
            if len(result) > 0:
                result.append(None)
    return ', '.join([x for x in result[:granularity] if x is not None])

def alert(message):
    """
        Alerts all players on the server with a message
    """
    print(f"Server Alert: {message}")
    SayText2(f"{ORANGE}Server Alert{WHITE}: {message}").send()
    for player in PlayerIter('human'):
        player.play_sound("ui/system_message_alert.wav")