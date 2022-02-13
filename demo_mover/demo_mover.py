# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
from listeners.tick import GameThread
from listeners import OnLevelInit

# Core Imports
import os

# 3rd Party Imports
pass

TF_ROOT = "/home/tf/tf/"

@OnLevelInit
def on_level_init(name):
    global TF_ROOT
    for file_name in os.listdir(TF_ROOT):
        if file_name.endswith(".dem"):
            demo_info = file_name.split("-")
            map_name = demo_info[3]

            if not name == map_name:
                src = os.path.join(TF_ROOT, file_name)
                dest = os.path.join(TF_ROOT, "demos_finished", file_name)
                print(f"Moving {src} to {dest}")

                os.rename(src, dest)