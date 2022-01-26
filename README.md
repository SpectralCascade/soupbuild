# soupbuild
My all-in-one native application build pipeline. Deals with all the mess that comes with dependency soup.

Requires Python version 3.8 or newer. Developed primarily for Windows but could easily be ported to Unix.

## Usage
1. Setup a build configuration file (JSON with .soup file extension).
2. Run soupbuild.py from the directory containing the build configuration file:

`python3 soupbuild.py [options] [platform] [task-name] [mode]`

Running the script without any arguments runs the default task set in the build configuration file.

## Build configuration file (.soup)
The build configuration file defines how soupbuild will perform tasks for different platforms and modes.
You can add custom platforms and modes (e.g. Debug or Release) which can then be customised to suit your needs.
An example file is included in the root directory named `demo.soup`.

## Option flags:
- `--quiet` means only the task result and stdout from subprocesses are shown.
- `--task-only` means that the task is run without any pre-task setup processes.
- `--init` reinitialises the work directory.
