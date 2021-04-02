# Flux build system
Simple, experimental build system for C/C++ projects, written in Python!

⚠️ _currently **work in progress**, everything may change or break at any time._

Strongly inspired by [**fips**](https://github.com/floooh/fips) build system and [**wake**](https://github.com/wonkey-coders/wonkey) build system from wonkey programming language.

## What's Flux

Flux is a Python command line tool which provides an *integrated build environment* for C/C++ projects by wiring together existing build tools.

## An 'integrated build environment'

Flux doesn't reinvent the wheel by implementing yet another build system from scratch, but instead wires existing tools together:

- **python** to run commands and code generation scripts
- based on very fast **ninja** build system
- used custom **yaml** files to describe how to generate and build projects
- **git** to fetch external dependencies
- and of course **C/C++ toolchain** (gcc, msvc)

## Multi- and cross-platform support

Flux can mainly build on **Windows**, **Linux**, **MacOS**, **Raspbian** and cross-compile to **iOS**, **Android** and **Emscripten**.

## What Flux is not

- Flux is not a build job scheduler like *Jenkins*, *Hudson*, *msbuild* or *ant*
- Flux is not a distributed build system like *Incredibuild*
- Flux is not a replacement for *cmake*, *premake* or *scons*

# Get started

## You need

- **python** (2.7.x or 3.x should both work) to execute scripts
- a working C/C++ development environment:
    - on **MacOS**: *XCode* and *Command Line Tools* (CLT)
    - on **Linux**: *gcc* (or *clang*)
    - on **Windows**: *mingw* or *Visual Studio 2015* or better
- and **ninja** build system, can be installed:
    - on **MacOS**: `brew install ninja` (*Homebrew*)
    - on **Linux**: `apt-get install ninja-build` (*Debian/Ubuntu*)
    - on **Windows**: `scoop install ninja` (*scoop*) or `choco install ninja` with (*chocolatey*)
    - other systems, see this page ["Pre-built Ninja packages"](https://github.com/ninja-build/ninja/wiki/Pre-built-Ninja-packages)

## Get Flux

Flux will create additional directories on the same directory level as the Flux directory itself, thus it is recommended to `git clone` Flux into a separate **workspace** directory:

```cmd
> cd ~
> mkdir my-workspace
> cd my-workspace
> git clone https://github.com/seyhajin/flux.git
> cd flux
```

## Project directory structure

Flux considers its parent folder to be its **workspace** directory, and it always refers to that folder to launch commands.

```
┃
┗━━ 📁 <flux-workspace>/
    ┃
    ┗━━ 📁 flux/
    ┃   ┃
    ┃   ┗━━ flux            # flux executable
    ┃   ┃
    ┃   ┗━━ ...
    ┃
    ┗━━ 📁 project-1/
    ┃   ┃    
    ┃   ┣━━ flux.yml
    ┃   ┃    
    ┃   ┗━━ ...
    ┃
    ┗━━ 📁 modules/
        ┃
        ┗━━ 📁 core/
        ┃   ┃
        ┃   ┗━━ flux.yml
        ┃   ┃    
        ┃   ┗━━ ...
        ┃
        ┗━━ 📁 sdl2/
            ┃
            ┗━━ flux.yml
            ┃    
            ┗━━ ...
```

## Test if Flux works

Invoke the Flux main script by running `./flux` from within the **flux** directory, you should see its help using:

**NOTE:** *on Windows, run `flux` instead of `./flux`*

```cmd
> ./flux
flux <version>

usage:  flux [verb] [opts] [projects]

...

info: run `flux help` for more informations
```

## Build projects

*TODO*

```cmd
./flux build mods/hello samples/hello
```
---
## How to Flux works

Flux needs to know the build options to determine the target of one or more projects. It will generate for each project, a `flux-proj/<target-build-profile>` directory and a `build.ninja` file to be able to compile the project.

[![](https://mermaid.ink/img/eyJjb2RlIjoiZ3JhcGggVERcbkFbQnVpbGRPcHRzXVxuQltUYXJnZXRPcHRzXVxuQ1tQcm9qZWN0T3B0c11cbkRbR2VuZXJhdGUgTmluamFdXG5FW0J1aWxkIE5pbmphXVxuQSAtLT4gQiAtLT4gQyAtLT4gRCAtLT4gRSIsIm1lcm1haWQiOnsidGhlbWUiOiJkZWZhdWx0In0sInVwZGF0ZUVkaXRvciI6ZmFsc2V9)](https://mermaid-js.github.io/mermaid-live-editor/#/edit/eyJjb2RlIjoiZ3JhcGggVERcbkFbQnVpbGRPcHRzXVxuQltUYXJnZXRPcHRzXVxuQ1tQcm9qZWN0T3B0c11cbkRbR2VuZXJhdGUgTmluamFdXG5FW0J1aWxkIE5pbmphXVxuQSAtLT4gQiAtLT4gQyAtLT4gRCAtLT4gRSIsIm1lcm1haWQiOnsidGhlbWUiOiJkZWZhdWx0In0sInVwZGF0ZUVkaXRvciI6ZmFsc2V9)

## Targets

Flux contains the main various build parameters of the target platforms described in yaml files found in its `./flux/targets` folder. It will be possible to customize them by project (planned).

At the moment, there as targets for:
- [x] *macos.yml*
- [x] *windows.yml* (mingw)
- [x] *windows-msvc.yml* (msvc)
- [ ] *linux.yml*
- [ ] *raspbian.yml*

Flux target file use custom YAML tags, see [Flux YAML custom tags](#Flux-YAML-custom-tags)

### Target file references

| yaml | default | values| description |
|:--|:--|:--|:--|
|`target`|||Specifies target name, must be the same of filename (can also use `-` for separated words, e.g. `windows-msvc`)|
|`toolchain`|gcc||Specifies target name, must be the same of filename (may be `gcc` or `msvc`)|
|`msvc-version`|[2019, 2017, 2015]||Specifies array to auto-detect MSVC installation. The first found is taken. For **msvc** toolchain only.|
|`msvc-prefix`|Note: including file:||Specifies the ninja `msvc_deps_prefix` to filter `/showIncludes` output. For **msvc** toolchain only.|
|`commands`|||Can contains `cc`, `cxx`, `ar`, `as` executables|
|`options`|||Can contains `cc`, `cxx`, `ar`, `as` options to pass to command|
|`rules`|||Can contains `cc`, `cxx`, `ar`, `as` rules to generate ninja build file|
|`cc`, `cxx`, `ar`, `as`|||Use `!concat` or aliases to specifies parameters|

## Projects

Flux project contains all informations to build project described in yaml file named `flux.yml` (or `<dirname>.yml` or `<dirname>.flux`).

Flux project file use custom YAML tags, see [Flux YAML custom tags](#Flux-YAML-custom-tags)

### Project file references

| yaml | default | values | description |
|:--|:--|:--|:--|
|`build`|`app`|[`app`, `mod`, `lib`]|Specifies project build type. Considers `mod` is *static lib* and `lib`is *shared lib* (planned for `lib`). You can also use the following aliases: `application` for `app`, `module` or `staticlib` for `mod`, `library` or `sharedlib` for `lib`|
|`type`|`window`|[`window`, `console`]|Specifies only if `build` is `app`.|
|`name`|||Name of project. Recommanded use the same name of project folder (can also use `-` for separated words, e.g. `sdl2-image`)|
|`about`|||Optional. Brief description of project|
|`support`|||Optional. Link of project website|
|`options`|||Optional. Can contains `cc`, `cxx`, `ar`, `as` project options|
|`cc`, `cxx`, `ar`, `as`|||Use `!concat` or aliases to specifies parameters|
|`inputs`|||Most important, determines the project inputs. see [Project inputs](#project-inputs) for more informations|

### Project inputs

Flux input use two types: `system` and `local` (identical to C/C++).
The `system` input must be between `<...>`, e.g. `<libsdl2.a>` will added the `sdl2` library in the linking options.

#### Assets

Flux copy each files to target destination after the target build sucess. Flux search `@/` separator and determine *source* and *destination*: `src@/dst`. 

*NOTE: Input type is `local` from project directory.*

Example:
```yaml
- assets@/assets
```
Each files in current project `assets` directory will be copied to `flux-proj/<target-build-profile>/assets` directory.

#### Include directories

Flux add project include directory to C/C++ options during compilating. Input must be ends with `*.h` to determine that *include directory*.

*NOTE: Input type is `local` from project directory.*

Example:
```yaml
- SDL/include/*.h
```

#### Library directories

Flux add project library directory to C/C++ options during linking. Input must be ends with `*.a` or `*.lib` to determine that *library directory*.

*NOTE: Input type is `local` from project directory.*

Examples:
```yaml
- lib/*.a 
- lib/*.lib
```

#### Sources

Flux add project source to C/C++ options during compiling. Input can have these extensions:

| extension | description |
|:--|:--|
|`.c`|C source file|
|`.cc`, `.cxx`, `.cpp`, `.c++`|C++ source file|
|`.m`|Objective-C source file|
|`.mm`|Objective-C++ source file|
|`.asm`, `.s`|Assembler source file|
|`.java`|Java source file (soon for Android target)|

We can use *wilcard* to specifes multiple source files, e.g :
* `/*.c` : get all files with `.c` extension from directory
* `/**/*.c` : get all files with `.c` extension recursively from directory (use with caution)

*NOTE: Input type is `local` from project directory.*

Examples:
```yaml
- SDL/src/*.c
- !?macos SDL/src/video/cocoa/*.m
```

#### Libraries

Flux add library to C/C++ project during linking. Input can have these extensions:

| extension | description |
|:--|:--|
|`.a`, `.lib`, `.dylib`|Library file (`local` or `system`)|
|`.framework`, `.weak_framework`|MacOS Framework (`local` or `system`)|
|`.so`, `.dll`, `.dylib`|Dynamic library file (`local` only)|
|`.exe`|Executable file (`local` only)|

We can use *wilcard* to specifes multiple library files for `local` input only, e.g :
* `/*.a` : get all files with `.a` or `.lib` extension from directory
* `/**/*.a` : get all files with `.a` or `.lib` extension recursively from directory (use with caution)

*NOTE: Input type is `local` from project directory or `system`*

Examples:
```yaml
- !?macos <Metal.framework>  # add '-framework Metal' in link options for MacOS target
- !?windows <libuser32.a>    # add '-luser32' in link options for Windows target
```

#### Modules

Flux project can use other Flux modules. Input type must be `system` and ends with `.flux` extension.
A Flux module is a static library, interconnected between them. It is better to use them to save compilation time and have an orderly workspace.

*NOTE: Input type is `system` from workspace directory*

Examples:
```yaml
- <mods/sx/sx.flux>       # import 'sx' module into my project
- <mods/sdl2/sdl2.flux>   # import 'sdl2' module into my project
```

In project source, e.g. :
```c++
#include <mods/sx/sx.h>
#include <mods/sdl2/SDL/include/SDL.h>
```
---
### Flux YAML custom tags

**Yaml** files use custom tags to be extensible, easy to read and understand:

- `!concat`: concatenate sequence (array) values into single string separated by space.
- `!flags`, `!opts` and `!args`' are aliases of `!concat` tag.
- `!?linux`, `!?macos`, `!?windows` filter the values according to the **target platform** during generate/build time. *(others are planned)*
- `!?debug`, `!?release` filter the values according to the **target configuration**
- `!?x86`, `!?x64`, `!?arm32`, `!?arm64`, `!?wasm` filter the values according to the **target architecture**
- `!?gcc`, `!?msvc`filter the values according to C/C++ toolchain
- `!$env` replace all environment variables found in value that are between `${...}`
- `!join` allows to concatenate a file system path from the sequence (`os.path.sep.join(seq)`)

Extract from **windows-msvc** target:
```yaml
target: windows
toolchain: msvc

# commands
commands:
  cc: cl
  cxx: cl
  as: !concat                       # works like `switch`
    - !?x86 ml                      # use for 'x86' target arch
    - !?x64 ml64                    # use for 'x64' target arch
  ar: lib
  ld: link

# options
options:
  cc: !opts                         # mandatory if you want to use build filters below
    - -std=gnu99                    # global options
    - -D_WIN32_WINNT=0x0603         # global options, can be in single line
    - !?x64 -m64 -Wa,-mbig-obj      # only for 'x64' target arch
    - !?debug -O2                   # only for 'debug' target config
    - !?release -O3 -DNDEBUG=1      # only for 'release' target config
...
```

If we built in `x86` architecture and `debug` mode, we would have the following `cc` options:
```
options.cc = -std=gnu99 -D_WIN32_WINNT=0x0603 -O2
```