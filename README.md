# soupbuild
My all-in-one native application build pipeline. Deals with all the mess that comes with dependency soup.

Requires Python version 3.8 or newer. Developed primarily for Windows but could easily be ported to Unix.

## Usage
1. Setup a build configuration file (JSON with .soup file extension).
2. Run soupbuild.py from a directory containing the build configuration file:

`python3 soupbuild.py [options] [platform] [task-name] [mode]`

Running the script without any arguments runs the default task set in the build configuration file.

For an example project using soupbuild, check out [plumbing_disaster](https://github.com/SpectralCascade/plumbing_disaster) which has a build file setup for building the app for Windows and Android.

## Build configuration file (.soup)
The build configuration file defines how soupbuild will perform tasks for different platforms and modes.
You can add custom platforms and modes (e.g. Debug or Release) which can then be customised to suit your needs.
An example is included in the root directory of [plumbing_disaster](https://github.com/SpectralCascade/plumbing_disaster) named `build.soup`.

## Options:
- `--build-config="path/to/config/file/example.soup"` provide a path to a specific build configuration file.
- `--init` reinitialises the work directory.
- `--quiet` means only the task result and stdout from subprocesses are shown.
- `--skip-deps` skips the dependency retrieval and setup processes.
- `--task-only` means that the task is run without any pre or post-task processes.
