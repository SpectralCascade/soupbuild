#!/usr/bin/env python3

import sys
import os
import json
from types import SimpleNamespace

def format_config(config, d, platform, mode, root):
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = format_config(config, d[k], platform, mode, root)
        elif isinstance(v, str):
            d[k] = d[k].replace("{name}", config["name"])
            d[k] = d[k].replace("{output}", config["output"])
            d[k] = d[k].replace("{mode}", mode)
            d[k] = d[k].replace("{platform}", platform)
            d[k] = d[k].replace("{root}", root)
    return d

def execute(command):
    print("\n> " + command)
    os.system(command)

# Standard execution (in directory with a .soup file):
# python3 soupbuild.py [platform] task [mode]
if __name__ == "__main__":
    print("I'm at SOUP!")
    cwd = os.getcwd()
    argc = len(sys.argv)
    
    config = None
    for file in os.listdir("."):
        if (file.endswith(".soup")):
            with open(file, 'r') as data:
                config = json.loads(data.read())
            break
    if (config == None):
        print("Failed to find configuration file in CWD \"" + cwd + "\", aborting soupbuild.")
        sys.exit(-1)
    
    
    argi = 1
    
    # Get the platform target
    platform = config["default-platform"]
    if (argi < argc and sys.argv[argi] in config["platforms"]):
        platform = sys.argv[argi]
        argi += 1
    
    # Get the task
    task = config["default-task"]
    if (argi < argc and sys.argv[argi] in config["platforms"][platform]["tasks"]):
        task = sys.argv[argi]
        argi += 1
    
    # Get the mode
    mode = config["default-mode"]
    if (argi < argc and sys.argv[argi] in config["modes"]):
        mode = sys.argv[argi]
        argi += 1
    
    print("Executing task \"" + task + "\" for platform \"" + (platform if len(platform) > 0 else "[all platforms]") + "\" in mode \"" + (mode if len(mode) > 0 else "[none]") + "\".")
    
    platforms = []
    if (len(platform) == 0):
        # All platforms
        for key, value in config["platforms"]:
            platforms.append(key)
    else:
        platforms.append(platform)
    
    original_config = config.copy()
    for platform in platforms:
        # Format config
        format_config(config, config, platform, mode, cwd)
        
        # First get the template project copied to the working directory
        src = config["platforms"][platform]["template"]["project"]
        dest = config["work"] + "/" + os.path.split(config["platforms"][platform]["template"]["project"])[-1]
        execute("mkdir \"" + dest + "\"")
        execute("copy \"" + src + "\" \"" + dest + "\"")

        # Now insert source and assets
        
    
