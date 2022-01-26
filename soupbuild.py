#!/usr/bin/env python3

import sys
import os
import time
import json
from types import SimpleNamespace

MAJOR_VERSION = 1
MINOR_VERSION = 0

def format_config(config, d, platform, mode, root):
    for k, v in d.items():
        if isinstance(v, dict):
            print("Key " + k + " is a dict, recursing...")
            d[k] = format_config(config, d[k], platform, mode, root)
        elif isinstance(v, str):
            print("Formatting value of key " + k)
            d[k] = d[k].replace("{name}", config["name"])
            d[k] = d[k].replace("{output}", config["output"])
            d[k] = d[k].replace("{mode}", mode)
            d[k] = d[k].replace("{platform}", platform)
            d[k] = d[k].replace("{root}", root)
    return d

def execute(command):
    print("> " + command)
    return os.system(command)

# Standard execution (in directory with a .soup file):
# python3 soupbuild.py [platform] task [mode]
if __name__ == "__main__":
    print("Soupbuilder version " + str(MAJOR_VERSION) + "." + str(MINOR_VERSION))
    cwd = os.getcwd()
    argc = len(sys.argv)
    
    config = None
    for file in os.listdir("."):
        if (file.endswith(".soup")):
            with open(file, 'r') as data:
                config = json.loads(data.read())
            break
    if (config == None):
        print("\nFailed to find configuration file in CWD \"" + cwd + "\", aborting soupbuild.")
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
    
    print("\nSoupbuild running with task \"" + task + "\" for platform \"" + (platform if len(platform) > 0 else "[all platforms]") + "\" in mode \"" + (mode if len(mode) > 0 else "[none]") + "\".")
    
    platforms = []
    if (len(platform) == 0):
        # All platforms
        for key, value in config["platforms"]:
            platforms.append(key)
    else:
        platforms.append(platform)
    
    original_config = config.copy()
    for platform in platforms:
        start_time = time.time()
    
        # Format config
        format_config(config, config, platform, mode, cwd)
        
        # First get the template project copied to the working directory
        print("\nCopying template project...")
        src = config["platforms"][platform]["template"]["project"]
        dest = config["work"] + "/" + os.path.split(config["platforms"][platform]["template"]["project"])[-1]
        execute("mkdir \"" + dest + "\"")
        execute("copy \"" + src + "\" \"" + dest + "\"")
        
        # Now link source code and assets - more efficient than copying.
        print("\nLinking source and asset directories...")
        full_code_dest = config["platforms"][platform]["template"]["source"]
        full_assets_dest = config["platforms"][platform]["template"]["assets"]
        code_dest = "\"" + os.path.join(dest, os.path.split(full_code_dest)[0]) + "\""
        assets_dest = "\"" + os.path.join(dest, os.path.split(full_assets_dest)[0]) + "\""
        full_code_dest = "\"" + os.path.join(dest, full_code_dest) + "\""
        full_assets_dest = "\"" + os.path.join(dest, full_assets_dest) + "\""
        
        execute("mkdir " + code_dest)
        execute("mkdir " + assets_dest)
        execute("mklink /J " + full_code_dest + " \"" + config["source"] + "\"")
        execute("mklink /J " + full_assets_dest + " \"" + config["assets"] + "\"")
        
        # Finally, execute the task steps in the working project directory
        print("\nRunning task \"" + task + "\" for platform: " + platform)
        execute("cd \"" + dest + "\"")
        steps = config["platforms"][platform]["tasks"][task]
        num_steps = len(steps)
        
        failed = False
        for i in range(num_steps):
            print("\nStep " + str(i + 1) + " of " + str(num_steps))
            if (execute(steps[i]) != 0):
                failed = True
                break
        
        # Return to root directory
        execute("cd \"" + cwd + "\"")
        
        print("\n\nTask \"" + task + "\" " + ("FAILED" if failed else "COMPLETED SUCCESSFULLY") + " in " + ("{:.2f}".format(time.time() - start_time)) + " seconds for platform: " + platform)
