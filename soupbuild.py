#!/usr/bin/env python3

import sys
import os
import re
import time
import json
import shutil

MAJOR_VERSION = 1
MINOR_VERSION = 0
APP_NAME = "Soupbuild"

quiet = False
start_time = 0
script_path = ""
config_path = ""
cwd = ""
app_data = ""

# Log a message to the console if not running with the --quiet flag
def log(message):
    if (not quiet):
        log_always(message)

# Always log no matter what
def log_always(message):
    print(("[{:.3f}] ".format(time.time() - start_time)) + message)

def GetAppDataPath():
    if sys.platform == 'win32':
        return os.path.join(os.environ['LOCALAPPDATA'], APP_NAME)
    elif sys.platform == 'darwin':
        from AppKit import NSSearchPathForDirectoriesInDomains
        return os.path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], APP_NAME)
    return os.path.expanduser(os.path.join("~", "." + APP_NAME))

# Applies task level formatting to strings
def format_vars(data, config, mode, platform, root):
    data = data.replace("{name}", config["name"])
    data = data.replace("{output}", config["output"])
    data = data.replace("{mode}", mode)
    data = data.replace("{platform}", platform)
    data = data.replace("{root}", root)
    data = data.replace("{work}", config["work"])
    data = data.replace("{app_data}", app_data)
    data = data.replace("{cpu_count}", str(os.cpu_count()))
    return data

# Format the build configuration data with task level formatting
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

# Execute a shell command
def execute(command, ps = False):
    log("$ " + command)
    return os.system(("powershell.exe " if ps else "") + command)

# URL retrieval progress callback
def handle_download(block_count, block_size, total_size):
    log("Downloaded " + str(block_size * block_count) + " / " + (str(total_size) if total_size >= 0 else "unknown total") + " bytes...")

# Downloads an archive and extracts it to a folder
def retrieve_archive(url, name, root=".", v="", force=False):
    if not os.path.exists(root):
        execute("mkdir \"" + root + "\"")
    os.chdir(root)
    url = url.format(version=v)
    tarball = url.endswith(".tar.gz")
    ext = (".tar.gz" if tarball else ".zip")
    extracted = name + ("-" + v if v else "")
    if not os.path.exists(extracted):
        execute("mkdir \"" + extracted + "\"")
    elif not force:
        log("Already downloaded version " + v + " of dependency " + name + " from " + url)
        os.chdir(extracted)
        return extracted
    os.chdir(extracted)
    log("Attempting to download archive from URL " + url)
    try:
        # Note: this urlretrieve function may get deprecated in future python versions
        urllib.request.urlretrieve(url, "archive" + ext, handle_download)
        log("Download successful, extracting to \"" + extracted + "\"")
        execute("tar -x" + ("vz" if tarball else "") + "f archive" + ext)
        os.remove("archive" + ext)
        # If there's only a single folder, move extracted files out of it
        extracted_list = os.listdir(os.getcwd())
        if len(extracted_list) == 1 and os.path.isdir(extracted_list[0]):
            for item in os.listdir(extracted_list[0]):
                execute("mv \"" + extracted_list[0] + "/" + item + "\" . -Force", ps=True)
            os.rmdir(extracted_list[0])
    except Exception as e:
        log("ERROR: Failed to download and extract archive due to exception: " + str(e))
        return ""
    return extracted

# Standard execution (in directory with a .soup file):
# python3 soupbuild.py [platform] task [mode]
if __name__ == "__main__":
    # Initial variables setup
    start_time = time.time()
    cwd = os.getcwd()
    script_path = os.path.abspath(sys.argv[0])
    argc = len(sys.argv)
    argi = 1
    source_extensions = [".cpp", ".c"]
    header_extensions = [".h"]
    app_data = GetAppDataPath()
    if not os.path.exists(app_data):
        execute("mkdir \"" + app_data + "\"")
    
    # Get command flags and options
    quiet = "--quiet" in sys.argv
    task_only = "--task-only" in sys.argv
    init = "--init" in sys.argv
    skip_deps = "--skip-deps" in sys.argv
    
    config = None
    while (argi < argc and sys.argv[argi].startswith("--")):
        if (sys.argv[argi].startswith("--build-config=")):
            file = sys.argv[argi][15:]
            with open(file, 'r') as data:
                config = json.loads(data.read())
                config_path = os.path.abspath(file)
        argi += 1
    
    # Show program version
    if (not quiet):
        version_str = str(MAJOR_VERSION) + "." + str(MINOR_VERSION)
        border = "////////////////" + ("/" * len(version_str))
        print(border)
        print("/ SOUPBUILDER " + version_str + " /")
        print(border + "\n")
    
    # Version checking; shutil.rmtree() deletes junction link contents in older versions, which we don't ever want to happen.
    python_version_info = sys.version_info
    if (python_version_info[0] < 3 or (python_version_info[0] == 3 and python_version_info[1] < 8)):
        print("ERROR: Python version must be 3.8 or newer, current version is " + sys.version.split(' ')[0])
        sys.exit(-1)
    
    # Import python3 libraries
    import urllib.request
    
    # Find and load the build configuration file
    if (config == None):
        for file in os.listdir("."):
            if (file.endswith(".soup")):
                with open(file, 'r') as data:
                    config = json.loads(data.read())
                    config_path = os.path.abspath(file)
                break
        if (config == None):
            print("ERROR: Failed to find build configuration file in current working directory \"" + cwd + "\", aborting.")
            sys.exit(-1)
    
    # Remove pre-existing work and output directory trees when initialising
    if (init and os.path.exists(config["work"])):
        try:
            shutil.rmtree(config["work"])
            shutil.rmtree(config["output"])
        except:
            print("ERROR: Unknown error occurred while initialising work directory")
            sys.exit(-1)
    
    # Setup other config variables
    if ("source-ext" in config):
        source_extensions = config["source-ext"].copy()
    if ("header-ext" in config):
        header_extensions = config["header-ext"].copy()
    
    # Get the platform target
    platform = config["default-platform"]
    if (argi < argc and sys.argv[argi] in config["platforms"]):
        platform = sys.argv[argi]
        argi += 1
    if (platform == None or platform == ""):
        print("ERROR: No platform is specified. Either specify when running this script or add \"default-platform\" field to the config file.")
        sys.exit(-1)
    
    # Get the task
    task = config["default-task"]
    if (argi < argc and sys.argv[argi] in config["platforms"][platform]["tasks"]):
        task = sys.argv[argi]
        argi += 1
    if (platform == None or platform == ""):
        print("ERROR: No task is specified. Either specify when running this script or add \"default-task\" field to the config file.")
        sys.exit(-1)
    
    # Get the mode
    mode = config["default-mode"] if "default-mode" in config else ""
    if (argi < argc and sys.argv[argi] in config["modes"]):
        mode = sys.argv[argi]
        argi += 1
    
    log("Running task \"" + task + "\" for platform: " + (platform if len(platform) > 0 else "[all platforms]") + " in mode \"" + (mode if len(mode) > 0 else "[none]") + "\".")

    # Add target platform(s) to list
    platforms = []
    if (len(platform) == 0):
        # All platforms
        for key, value in config["platforms"].items():
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
        
        all_source_files_separator = " "
        all_source_files_formatter = "\"{source_file}\""
        all_header_files_separator = " "
        all_header_files_formatter = "\"{header_file}\""
        
        all_includes_separator = " "
        all_includes_formatter = "\"{include_dir}\""
        
        # Format config before use
        format_config(config, config, platform, mode, cwd)
        
        # Pre-task steps, must setup working project directory if not already done.
        src = config["platforms"][platform]["template"]["project"]
        dest = os.path.join(config["work"], os.path.split(config["platforms"][platform]["template"]["project"])[-1])
        if (not task_only):
            # Automagically download & setup dependencies
            os.chdir(app_data)
            if "dependencies" in config["platforms"][platform]:
                for dep in config["platforms"][platform]["dependencies"]:
                    key = dep["name"]
                    version = ""
                    if "version" in dep:
                        version = dep["version"]
                    if not skip_deps:
                        # Shared library prioritised over building from source
                        if "shared" in dep:
                            # Download and extract shared library if necessary
                            if not retrieve_archive(dep["shared"], key, "shared", version):
                                sys.exit(-1)
                            os.chdir(app_data)
                        if "source" in dep:
                            # Download and extract library source code if necessary
                            extract_dir = retrieve_archive(dep["source"], key, "source", version)
                            if not extract_dir:
                                sys.exit(-1)
                            elif "build" in dep:
                                # Build the library if necessary
                                for build_step in dep["build"]:
                                    execute(build_step, ps=True)
                            os.chdir(app_data)
            os.chdir(cwd)
            
            # Make sure output directory exists
            output_dir = os.path.join(config["output"], platform, mode)
            if (not os.path.exists(output_dir)):
                execute("mkdir \"" + output_dir + "\"")
                execute("cp -R -Force \"" + src + "\" \"" + dest + "\"", ps=True)
            else:
                execute("cp -R -Force \"" + src + "\" \"" + os.path.split(dest)[0] + "\"", ps=True)
            
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
            
            # Next, grab lists of the source & asset file paths as well as dependency paths
            source_files = []
            header_files = []
            asset_files = []
            include_paths = []
            lib_paths = []

            # Excluded source file paths
            excluded_source_files = config["source-ignore"] if "source-ignore" in config else []
            if "source-ignore" in config["platforms"][platform]:
                excluded_source_files = excluded_source_files + config["platforms"][platform]["source-ignore"]
            excluded_source_files = [os.path.normpath(path) for path in excluded_source_files]

            # Excluded asset file paths
            excluded_asset_files = config["assets-ignore"] if "assets-ignore" in config else []
            if "assets-ignore" in config["platforms"][platform]:
                excluded_asset_files = excluded_asset_files + config["platforms"][platform]["assets-ignore"]
            excluded_asset_files = [os.path.normpath(path) for path in excluded_asset_files]
            
            # Source and header files
            for root, dirs, files in os.walk(config["source"]):
                root = os.path.normpath(root)
                dirs[:] = [dir for dir in dirs if os.path.join(root, dir) not in excluded_source_files]
                for file in files:
                    if (file in excluded_source_files):
                        continue
                    found_file = False
                    for ext in source_extensions:
                        if (file.endswith(ext)):
                            source_files.append(os.path.join(root, file))
                            found_file = True
                            break
                    if (not found_file):
                        for ext in header_extensions:
                            if (file.endswith(ext)):
                                header_files.append(os.path.join(root, file))
                                break
            
            # Asset files
            for root, dirs, files in os.walk(config["assets"]):
                root = os.path.normpath(root)
                for file in files:
                    if (file not in excluded_asset_files):
                        asset_files.append(os.path.join(root, file))
            
            log("Found " + str(len(source_files)) + " source file(s).")
            log("Found " + str(len(header_files)) + " header file(s).")
            log("Excluded " + str(len(excluded_source_files)) + " source/header path(s).")
            log("Found " + str(len(asset_files)) + " asset files.")
            log("Excluded " + str(len(excluded_asset_files)) + " asset path(s).")
            
            # Include and library linking paths
            dep_index = 0
            for dep in config["platforms"][platform]["dependencies"]:
                key = dep["name"]
                v = dep["version"]
                source_path = os.path.join(app_data, "source", key + ("-" + v if v else ""))
                if "includes" in dep:
                    for i in range(len(dep["includes"])):
                        config["platforms"][platform]["dependencies"][dep_index]["includes"][i] = os.path.join(source_path, dep["includes"][i].format(version=v)).replace(os.sep, '/')
                    include_paths = include_paths + dep["includes"]
                if "libs" in dep:
                    for i in range(len(dep["libs"])):
                        config["platforms"][platform]["dependencies"][dep_index]["libs"][i] = os.path.join(source_path, dep["libs"][i].format(version=v)).replace(os.sep, '/')
                    lib_paths = lib_paths + dep["libs"]
                dep_index += 1
            
            os.chdir(dest)
            
            # Now generation/formatting can begin
            loaded_files = []
            output_paths = []
            for formatter, data in config["platforms"][platform]["template"]["generate"].items():
                # Create the string lists as per specified formatters
                item_formatter = data["formatter"] if "formatter" in data else "\"{item}\""
                item_separator = data["separator"] if "separator" in data else " "
                
                if ("{all_source_files}" in data["value"]):
                    all_source_files = item_separator.join([item_formatter.format(item=source_file) for source_file in source_files])
                    data["value"] = data["value"].format(all_source_files=all_source_files)
                elif ("{all_header_files}" in data["value"]):
                    all_header_files = item_separator.join([item_formatter.format(item=header_file) for header_file in header_files])
                    data["value"] = data["value"].format(all_header_files=all_header_files)
                elif ("{all_include_paths}" in data["value"]):
                    all_include_paths = item_separator.join([item_formatter.format(item=include_path) for include_path in include_paths])
                    data["value"] = data["value"].format(all_include_paths=all_include_paths)
                elif ("{all_lib_paths}" in data["value"]):
                    all_lib_paths = item_separator.join([item_formatter.format(item=lib_path) for lib_path in lib_paths])
                    data["value"] = data["value"].format(all_lib_paths=all_lib_paths)
                
                # Load and format the files
                for path in data["paths"]:
                    template_path = os.path.join(cwd, config["platforms"][platform]["template"]["project"], path)
                    if (not os.path.exists(template_path)):
                        log("Warning: File at \"" + path + "\" does not exist. Skipping generation/formatting...")
                        continue
                    if (path not in output_paths):
                        output_paths.append(path)
                        with open(template_path, "r", encoding="utf-8") as infile:
                            formatted = infile.read()
                            formatted = formatted.replace("{" + formatter + "}", data["value"])
                            loaded_files.append(formatted)
                    else:
                        index = output_paths.index(path)
                        loaded_files[index] = loaded_files[index].replace("{" + formatter + "}", data["value"])
            # Write the files back out to the working project
            for i in range(len(output_paths)):
                with open(output_paths[i], "w") as file:
                    file.write(loaded_files[i])
            os.chdir(cwd)
        
        # Execute the task steps in the working project directory
        os.chdir(dest)
        task_run_dir = os.getcwd()
        
        steps = config["platforms"][platform]["tasks"][task]["steps"]
        num_steps = len(steps)
        
        failed = False
        abort_on_error = config["platforms"][platform]["tasks"][task]["abort_on_error"] if "abort_on_error" in config["platforms"][platform]["tasks"][task] else True
        for i in range(num_steps):
            log("Task \"" + task + "\" step " + str(i + 1) + " of " + str(num_steps))
            run_task = "{run_task}" in steps[i]
            if (run_task):
                os.chdir(cwd)
                steps[i] = steps[i].replace("{run_task}", "python3 \"" + script_path + "\" --quiet --task-only \"--build-config=" + config_path + "\"")
            
            failed_step = False
            if (execute(steps[i], ps=(not run_task)) != 0):
                failed = True
                failed_step = True
            
            os.chdir(task_run_dir)
            if (failed_step):
                log("ERROR: Failed to complete step " + str(i + 1) + " of " + str(num_steps) + " for task \"" + task + "\". " + ("Continuing as abort_on_error is set to False" if not abort_on_error else "Aborting task..."))
                if (abort_on_error):
                    break
        
        # Return to root directory
        os.chdir(cwd)
        
        # Follow the result of the task
        log_always("Task \"" + task + "\" " + ("FAILED" if failed else "SUCCEEDED") + " in " + ("{:.2f}".format(time.time() - task_start_time)) + " seconds for platform: " + platform)
        if (failed):
            print("")
            sys.exit(-1)
        else:
            # Copy specified output files to outputs directory on task completion
            if ("outputs" in config["platforms"][platform]["tasks"][task]):
                for path in config["platforms"][platform]["tasks"][task]["outputs"]:
                    src_path = os.path.normpath(os.path.join(cwd, dest, path))
                    dest_path = os.path.normpath(os.path.join(cwd, config["output"], platform, mode, os.path.split(path)[-1]))
                    # Delete pre-existing files before copying new outputs
                    if (os.path.exists(dest_path)):
                        if (os.path.isfile(dest_path)):
                            os.remove(dest_path)
                        else:
                            shutil.rmtree(dest_path)
                    if (os.path.exists(src_path)):
                        execute("cp -R \"" + src_path + "\" \"" + dest_path + "\"", ps=True)
                    else:
                        log("Warning: specified output path \"" + src_path + "\" does not exist, failed to copy.")
            
            if ("output_shared" in config["platforms"][platform]["tasks"][task] and config["platforms"][platform]["tasks"][task]["output_shared"]):
                # Also be sure to copy shared libraries to the outputs directory
                os.chdir(app_data)
                if not os.path.exists("shared"):
                    execute("mkdir \"shared\"")
                os.chdir("shared")
                for dep in config["platforms"][platform]["dependencies"]:
                    dep_name = dep["name"] + ("-" + dep["version"] if "version" in dep else "")
                    dest_path = os.path.normpath(os.path.join(cwd, config["output"], platform, mode))
                    for root, dirs, files in os.walk(dep_name):
                        for file in files:
                            if not file.endswith(".txt"):
                                execute("cp \"" + os.path.join(root, file) + "\" \"" + dest_path + "\"", ps=True)
        
        config = original_config.copy()
