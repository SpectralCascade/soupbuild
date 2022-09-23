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

### Platform Dependencies
Each platform may have a list of dependencies upon which your project relies. Most commonly these will be code libraries and APIs. When configured correctly, Soupbuild can take care of your dependencies automagically - from downloading source code, to building the dependency or copying shared libraries over to your project's output directory after building.

There are only a few parameters needed for configuring dependencies:

`name` - Mandatory - Specifies the unique name of the dependency. This name will be used in directory paths for the dependency and will appear in Soupbuild's standard output for identification purposes. It doesn't really matter what you call your dependencies, as long as you can identify them.

`version` - Mandatory - Specifies the particular version of the dependency to be used. This could be a (string) version number, a git commit SHA or simply the date you added or modified the dependency. Again, in general you can call this whatever you like - with the exception of any string starting with the keyword `latest`. This keyword indicates that Soupbuild should always try to obtain the latest version of the dependency, whether that's the latest commit of a git repo or an updated zip archive file. When used with git repositories, you can add a hyphen `-` followed by a particular branch name or commit SHA to specify a specific branch or commit to use.

`source` - Optional - Specifies the URL of a dependency's git repository, source code or development library archive. Soupbuild will use this URL to automagically download the dependency as necessary. You may use formatters in this field such as the dependency name and version.

`shared` - Optional - Specifies the URL of a dependency's prebuilt shared binaries (such as `.so` or `.dll` files). This must be a `.zip` or `.tar.gz` archive file.

`includes` - Mandatory - A list of relative paths from the root of the dependency archive/repository to the header include file(s).

`libs` - Mandatory - A list of relative paths from the root of the dependency archive/repository to the compiled library archive file(s). Note that if building from source, this is where any library archives will be output.

`build` - Optional - A list of terminal/shell/command line commands to execute when building the dependency from source. If you're building a library from source, you can specify the steps to do so here.

`clean` - Optional - A list of terminal/shell/command line commands to execute when cleaning the dependency files. If you're building a library from source, you can specify the steps to clean up the dependency so it can be rebuilt from scratch.

### Platform Source-ignore


### Platform Template
Templates enable you to give Soupbuild all the build system boilerplate you never want to touch again, such as native project files, generated Android studio files and anything else that makes you shudder to think about. How does it work? Well, you can create a folder hierarchy with these various build files in already; with some modifications to the files that enables Soupbuild to generate their content (such as absolute file paths to assets, source code and other stuff). Then, you can point Soupbuild towards your template folder hierarchy and files in the build configuration - that's where your platform template parameters come in.

`project` - Mandatory - Relative path to the template folder/file hierarchy. Typically it's best to keep this accessible in your project repository so you can commit changes to the native build system.

`source` - Mandatory - Relative path to your source code files within the template itself. Some build pipelines such as Android studio expect this to a specific place, such as "app/jni/src" while it may not matter so much for other build pipelines. Whatever you specify here will be created as a symbolic link in the file system to the "source" path specified in the global parameters during the build.

`assets` - Optional - Like "source" field noted above, but for project assets such as images, audio files and so on. Once again, this may be important to some build pipelines such as Android studio but matter less in other build pipelines. Whatever you specify here will be created as a symbolic link in the file system to the "assets" path specified in the global parameters during the build.

`generate` - Mandatory - This object contains custom objects for generating data that will replace sections of the template project files you specify. For example, you could use the generate field to insert a formatted list of source file paths into a make file, or the global name of the project. This takes all the effort out of adding, removing and modifying source files from your C/C++ project in future and enables you to ditch absolute paths as they can be generated each build instead.

#### Template Generate


### Platform Tasks
Platform specific tasks are what drive Soupbuild. Here you may specify a number of command steps to execute in the terminal/shell/command line to carry out a build, clean the project, run some custom pre and post build scripts or do anything else you can imagine. You can specify a unique name as the key for each task configuration, e.g. "build".

`steps` - Mandatory - A list of commands that are executed sequentially in the terminal/shell/command line when the task is run.

`outputs` - Optional - A list of paths to files or directories that should be copied into the global "output" directory upon task completion. For instance, if your build generates an executable file you can list the path to the file.

`output_shared` - Optional - A boolean that when set to true (default false) will copy the shared library binaries for each dependency (where relevant) into the global output directory upon task completion.

`abort_on_error` - Optional - A boolean that when set to false (default true) will cause the task to continue running in the event of an error, otherwise if set to true the task will stop when an error is encountered during one of the steps.

### Formatter variables
Certain configuration parameters may use so-called "formatter" variables, allowing you to insert some runtime defined values such as the project name, the number of logical CPU cores available to the machine, the current mode and so on. Not all of these formatters can be used everywhere, and some are dependent on scope (e.g. specifying the {name} formatter in a dependency URL will insert the name of the dependency, not the project).

Formatters are also used in generating project files from the template (as per the platform generate configurations)

`{name}` - The name of the project as defined by the global configuration parameters. When used in the scope of a platform dependency, instead the name of the dependency is used.

`{version}` - Only available in platform dependency scope; this is the `version` of the dependency.

`{output}` - Global `output` parameter, i.e. the path to which Soupbuild will output files upon completion of a task such as a build.

`{mode}` - The mode specified when the Soupbuild is run. This will be one of the modes specified in the global `mode` configuration object.

`{platform}` - The platform specified when the Soupbuild is run. This will be one of the platforms specified in the global `platforms` configuration object.

`{root}` - The absolute path of the working directory in which the build configuration file is.

`{work}` - Global `work` parameter, i.e. the directory where Soupbuild will work, generating files from the template and so on.

`{app_data}` - The shared Soupbuild local app data directory. On Windows this is in `%localappdata%/Soupbuild`.

`{cpu_count}` - The number of logical CPU cores available. This is useful when using the `-j` option with `make` builds, as it allows make to compile source files in parallel.
