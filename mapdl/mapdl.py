# Core Imports
from commands.typed import TypedSayCommand
from commands.typed import TypedServerCommand, TypedClientCommand
from listeners.tick import GameThread
from messages import SayText2
from colors import *
from cvars import ConVar

# Non Core imports
import requests
import tempfile
import os.path
import os
# import bz2
import re

# Console Variables
SV_MAPDL_PATH = None
TEXT_PREFIX = f"{WHITE}[{LIGHT_GREEN}MAPDL{WHITE}]"

def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = GameThread(target=fn, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
    return wrapper

# On Load
def load():
    global SV_MAPDL_PATH
    SV_MAPDL_PATH = ConVar("sv_mapdl_path", "tf/custom/mapdl/maps/")

    if not os.path.exists(SV_MAPDL_PATH.get_string()):
        os.makedirs(SV_MAPDL_PATH.get_string())

# Commands
@TypedClientCommand('mapdl')
@TypedServerCommand('mapdl')
def on_mapdl(command_info, map_url: str):
    if not map_url.startswith("http"):
        download_map(f"http://redirect.tf2maps.net/maps/{map_url}.bz2", command_info.index)
    else:
        download_map(map_url, command_info.index)

# Internal Functions
@threaded
def download_map(map_url, requester_index):
    if not requester_index:
        requester_index = 0

    SayText2(f"{TEXT_PREFIX} Searching for downloadable map...").send(requester_index)
    print("Searching for downloadable map...")

    # Direct Download
    if map_url.endswith(".bsp"):
        filename = re.search(r"[A-Za-z0-9_]+.bsp$", map_url).group()
        dest_path = os.path.join(os.getcwd(), f"{SV_MAPDL_PATH.get_string()}/{filename}")

        SayText2(f"{TEXT_PREFIX} Downloading map {filename}").send(requester_index)
        print(f"Downloading map {filename}")
        download_file(map_url, dest_path)

    # Direct download with bz2
    elif map_url.endswith(".bsp.bz2"):
        filename = re.search(r"([A-Za-z0-9_]+.bsp)(:?.bz2)$", map_url).groups()[0]
        dest_path = os.path.join(os.getcwd(), f"{SV_MAPDL_PATH.get_string()}/{filename}")
        temp_path = f"/tmp/{filename}.bz2"

        SayText2(f"{TEXT_PREFIX} Downloading map {filename}").send(requester_index)
        print(f"Downloading map {filename}")
        download_file(map_url, temp_path)
        unzip(temp_path, dest_path)

    # If attachment form data
    else:
        response = requests.head(map_url)
        attachment = response.headers['Content-Disposition']
        filename = re.search(r"[A-Za-z0-9_]+.bsp(.bz2)?", attachment).group()

        # Attachment is in bz2
        if filename.endswith(".bz2"):
            filename = filename.replace(".bz2", "")
            temp_path = f"/tmp/{filename}"
            dest_path = os.path.join(os.getcwd(), f"{SV_MAPDL_PATH.get_string()}/{filename}")

            SayText2(f"{TEXT_PREFIX} Downloading map {filename}").send(requester_index)
            print(f"Downloading map {filename}")
            download_file(map_url, temp_path)
            unzip(temp_path, dest_path)

        # Attachment is raw bytes
        elif filename.endswith(".bsp"):
            dest_path = os.path.join(os.getcwd(), f"{SV_MAPDL_PATH.get_string()}/{filename}")

            SayText2(f"{TEXT_PREFIX} Downloading map {filename}").send(requester_index)
            print(f"Downloading map {filename}")
            download_file(map_url, dest_path)

    SayText2(f"{TEXT_PREFIX} Downloaded map successfully!").send(requester_index)
    print(f"Downloaded map successfully!")


def download_file(url, dest_path):
    response = requests.get(url)
    response.raise_for_status()

    with open(dest_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)


def unzip(src, dest):
    with bz2.open(src, "rb") as src_file:
        with open(dest, "wb") as dest_file:
            dest_file.write(src_file.read())
