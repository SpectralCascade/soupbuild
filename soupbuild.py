#!/usr/bin/env python3

import sys
import os
import time
import json
import shutil

MAJOR_VERSION = 1
MINOR_VERSION = 0

quiet = False
start_time = 0

def log(message):
    if (not quiet):
        log_always(message)
    
def log_always(message):
    print(("[{:.3f}] ".format(time.time() - start_time)) + message)

def format_vars(data, config, mode, platform, root):
    data = data.format(
        name=config["name"],
        output=config["output"],
        mode=mode, platform=platform,
        root=root,
        run_task=("python3 " + os.path.join(root, "soupbuild.py") + " --quiet --task-only ")
    )
    return data

def format_config(config, d, platform, mode, root):
    for k, v in d.items():
        if isinstance(v, dict):
            #print("Key " + k + " is a dict, recursing...")
            d[k] = format_config(config, d[k], platform, mode, root)
        elif isinstance(v, list):
            for item in range(len(v)):
                if isinstance(v[item], dict):
                    #print("Key " + k + " is a list with a dict at index " + str(item) + ", recursing...")
                    d[k][item] = format_config(config, d[k][item], platform, mode, root)
                elif isinstance(v[item], str):
                    #print("Formatting value of key " + k + ", list element " + str(item))
                    d[k][item] = format_vars(d[k][item], config, mode, platform, root)
        elif isinstance(v, str):
            #print("Formatting value of key " + k)
            d[k] = format_vars(d[k], config, mode, platform, root)
    return d

def execute(command):
    log("$ " + command)
    return os.system(command)

# Standard execution (in directory with a .soup file):
# python3 soupbuild.py [platform] task [mode]
if __name__ == "__main__":
    # Initial variables setup
    start_time = time.time()
    cwd = os.getcwd()
    argc = len(sys.argv)
    argi = 1
    
    # Get command flags
    quiet = "--quiet" in sys.argv
    task_only = "--task-only" in sys.argv
    init = "--init" in sys.argv
    
    # Show program version
    if (not quiet):
        version_str = str(MAJOR_VERSION) + "." + str(MINOR_VERSION)
        border = "////////////////" + ("/" * len(version_str))
        print(border)
        print("/ SOUPBUILDER " + version_str + " /")
        print(border + "\n")
    
    # Version checking; shutil.rmtree() deletes junction link contents, which we don't ever want to happen.
    python_version_info = sys.version_info
    if (python_version_info[0] < 3 or (python_version_info[0] == 3 and python_version_info[1] < 8)):
        print("ERROR: Python version must be 3.8 or newer, current version is " + sys.version.split(' ')[0])
        sys.exit(-1)
    
    # Find and load the build configuration file
    config = None
    for file in os.listdir("."):
        if (file.endswith(".soup")):
            with open(file, 'r') as data:
                config = json.loads(data.read())
            break
    if (config == None):
        log("Failed to find build configuration file in current working directory \"" + cwd + "\", aborting.")
        sys.exit(-1)
    
    # Remove pre-existing work directory tree when initialising
    if (init and os.path.exists(config["work"])):
        try:
            shutil.rmtree(config["work"])
        except:
            log("Unknown ERROR occurred while initialising work directory")
            sys.exit(-1)
    
    # Skip flags
    while (argi < argc and sys.argv[argi].startswith("--")):
        argi += 1
    
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
    
    log("Running task \"" + task + "\" for platform: " + (platform if len(platform) > 0 else "[all platforms]") + " in mode \"" + (mode if len(mode) > 0 else "[none]") + "\".")

    # Add target platform(s) to list
    platforms = []
    if (len(platform) == 0):
        # All platforms
        for key, value in config["platforms"]:
            platforms.append(key)
    else:
        platforms.append(platform)
    
    # Iterate over each platform and execute the task
    original_config = config.copy()
    for platform in platforms:
        if (task not in config["platforms"][platform]["tasks"]):
            log("Task \"" + task + "\" does not exist for platform: " + platform)
            continue
        task_start_time = time.time()
        
        # Format config before use
        format_config(config, config, platform, mode, cwd)

        # Pre-task steps, must setup working project directory if not already done.
        src = config["platforms"][platform]["template"]["project"]
        dest = os.path.join(config["work"], os.path.split(config["platforms"][platform]["template"]["project"])[-1])
        if (not task_only):
            # First get the template project copied to the working directory
            if (not os.path.exists(dest)):
                execute("mkdir \"" + dest + "\"")
            execute("copy \"" + src + "\" \"" + dest + "\"")
            
            # Now link source code and assets - more efficient than copying.
            full_code_dest = config["platforms"][platform]["template"]["source"]
            full_assets_dest = config["platforms"][platform]["template"]["assets"]
            code_dest = os.path.join(dest, os.path.split(full_code_dest)[0])
            assets_dest = os.path.join(dest, os.path.split(full_assets_dest)[0])
            full_code_dest = os.path.join(dest, full_code_dest)
            full_assets_dest = os.path.join(dest, full_assets_dest)
            
            if (not os.path.exists(code_dest)):
                execute("mkdir \"" + code_dest + "\"")
            if (not os.path.exists(assets_dest)):
                execute("mkdir \"" + assets_dest + "\"")
            if (not os.path.exists(full_code_dest)):
                execute("mklink /J \"" + full_code_dest + "\" \"" + config["source"] + "\"")
            if (not os.path.exists(full_assets_dest)):
                execute("mklink /J \"" + full_assets_dest + "\" \"" + config["assets"] + "\"")
        
        # Execute the task steps in the working project directory
        log("Running task \"" + task + "\" for platform: " + platform)
        execute("cd \"" + dest + "\"")
        steps = config["platforms"][platform]["tasks"][task]
        num_steps = len(steps)
        
        failed = False
        for i in range(num_steps):
            log("Step " + str(i + 1) + " of " + str(num_steps))
            if (execute(steps[i]) != 0):
                failed = True
                break
        
        # Return to root directory
        execute("cd \"" + cwd + "\"")
        config = original_config.copy()
        
        # Show the result of the task
        log_always("Task \"" + task + "\" " + ("FAILED" if failed else "SUCCEEDED") + " in " + ("{:.2f}".format(time.time() - task_start_time)) + " seconds for platform: " + platform)
        if (failed):
            print("")
            sys.exit(-1)
