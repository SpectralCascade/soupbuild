# soupbuild
My all-in-one native application build pipeline. Deals with all the mess that comes with dependency soup.

Requires Python version 3.8 or newer. Developed primarily for Windows but could easily be ported to Unix.

## Usage
1. Setup a build configuration file (JSON with .soup file extension).
2. Run soupbuild.py from a directory containing the build configuration file:

`python3 soupbuild.py [options] [platform] [task-name] [mode]`

Running the script without any arguments runs the default task set in the build configuration file.

For an example project using soupbuild, check out [plumbing_disaster](https://github.com/SpectralCascade/plumbing_disaster) which has a build file setup for building the app for Windows and Android.

## Options:
- `--build-config="path/to/config/file/example.soup"` provide a path to a specific build configuration file.
- `--init` reinitialises the work directory.
- `--quiet` means only the task result and stdout from subprocesses are shown.
- `--skip-deps` skips the dependency retrieval and setup processes.
- `--skip-steps` skips all task steps
- `--task-only` means that the task is run without any pre or post-task processes.

## Build configuration file (.soup)
The build configuration file defines how soupbuild will perform tasks for different platforms and modes. This is written in [JSON](https://www.json.org/json-en.html).
You can add custom platforms and modes (e.g. debug & release) which can then be customised to suit your needs.
An example is included in the root directory of [plumbing_disaster](https://github.com/SpectralCascade/plumbing_disaster) named `build.soup`. The configuration file is at the heart of everything soupbuild can do. The rest of this documentation will focus on the fields and parameters you can specify in the build configuration to setup your build pipeline.

### Global parameters
At the topmost level, there are a number of global parameters for your project. Some of these options are mandatory, while others are optional and may be omitted.

`name` - Mandatory - Name of the project.

`source` - Mandatory - Relative path to the project source code (including header files where applicable).

`output` - Mandatory - Relative path for project outputs once Soupbuild has finished a task.

`work` - Mandatory - Relative path for Soupbuild to carry out filesystem work when in use.

`source-ext` - Optional - List of file extensions for C and C++ source files, by default `.c` and `.cpp`.

`header-ext` - Optional - List of file extensions for C and C++ header files, by default `.h`.

`source-ignore` - Optional - List of paths that should be ignored by Soupbuild when locating source code. This is useful if you support multiple platforms.

`assets` - Optional - Relative path to the project assets, other than source code (e.g. images, audio etc.)

`assets-ignore` - Optional - List of paths that should be ignored by Soupbuild when locating assets. This is useful if you support multiple platforms.

`default-platform` - Optional - Specify which platform should be used by default.

`default-mode` - Optional - Specify which mode should be used by default.

`default-task` - Optional - Specify which task should be used by default.

### Modes
Modes are useful when building variants of a program, such as a build with or without debug symbols. These modes mostly affect the native build systems Soupbuild uses, as you configure them to differ according to the mode used.

The `modes` field is a JSON object with custom mode objects specified as key-value pairs. At present the value objects have no significance or use, but the keys can  be used in a variety of situations such as when generating files from templates. Consider the mode used when running Soupbuild to be a variable, and those keys as the possible values. Typically you'll have debug and release modes, with the release mode build stripped of debugging symbols, as is standard practice with most C and C++ projects. But how you use modes is entirely up to you and how you implement them with your build system.

Soupbuild always requires at least one mode to be specified.

### Platforms
Platforms are at the heart of Soupbuild. Here, you can add custom platform-specific configurations for dependencies, project files and tasks. This allows you to port a project to any platform you want, while using the same Soupbuild interface to build them. Extremely flexible but provide a great deal of abstraction when dealing with all the gubbins of a typical C++ project.

Individual platforms can be specified with custom names as keys - for example, you might have "Windows" platform and "Android" platform configurations. Or you might call them something else entirely, like "PC" and "Mobile". It's up to you to decide what platforms you want to support and how to manage their respective build systems within Soupbuild. You could even use platforms as variations of the same program; for instance, you might have a platform variation that excludes some source files while including others.

Soupbuild always requires at least one platform to be specified.

Each platform has a number of configuration objects to be specified. These include the following:

`dependencies` - Optional - A list of objects specifying details about a particular project dependency, such as a shared or static library.

`source-ignore` - Optional - Platform specific list of paths to ignore when Soupbuild is locating source code files (including headers).

`template` - Mandatory - An object for configuring the platform's native build system project files, such as an Android studio project folder or some make files.

`tasks` - Mandatory - An object containing terminal/shell/command line task configurations. There must always be at least one task per platform.
