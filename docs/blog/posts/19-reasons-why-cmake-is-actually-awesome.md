---
date: 2019-12-09
categories:
  - Tools
authors:
  - kuba
comments: true
---

# 19 reasons why CMake is actually awesome

Topic of CMake is extremely controversial in the C/C++ community. People say that it is hard to properly set the include
paths, that syntax is archaic or that managing dependencies is a nightmare. Expressing public hate for CMake has become
a way of integrating with other software developers on the Internet.

And I partially understand that statements. Before CMake 3.x (aka Modern CMake) we were forced to use
`include_directories()` or manually set installation paths for libraries, that were not supported by default in CMake.
Syntax was a bit oldish and managing the compilation flags usually lead to headaches.

But since CMake 3.x (released on 06.2014) we have way more flexible and elegant ways of creating build systems with
CMake. Almost all cons are gone in favor of the new modern solutions. The only problem is that once a bad impression was
made, it is really hard to change it. After all, who would like to invest in studying new features and best practices of
a build system?! Well I do, and let me share with you 19 reasons, why CMake is actually awesome and you should give it a
try again.

<!-- more -->

!!! info

    For someone who is completely new to the topic: CMake is a build system generator, that creates build system files
    for common frameworks and IDE’s from a generic scripting language.


!!! note "Disclaimer"

    This article aims to give a brief overview of CMake capabilities without going deep into technical details. Consult
    the [official CMake docs][cmake-docs] for more details.

## 1. CMake is cross-platform

This one should be obvious since CMake has been cross-platform from the beginning. Currently it can run on all major
platforms:

- Windows,
- Linux,
- MacOS.

It means, that we can build projects which use CMake on all above platforms without additional platform-specific
configurations. No need to write Makefiles, configure Visual Studio projects, create custom Bash or batch files.
Everything is handled by CMake. Note, that I say “build on”, not “build for”. There is a clear separation between build
host and build target. Of course case when host and target is the same is assumed by default.

## 2. CMake supports multiple IDE’s and build frameworks

CMake is a build system generator (meta build system), which means that it creates configuration files for other
existing build systems. List of available options is dependent on the build host, which is natural (usually there is no
need to generate Visual Studio projects on Linux).

Below you can find a complete list (as for publication date) of all supported frameworks (CMake is calling them
generators):

- Borland Makefiles,
- MSYS Makefiles,
- MinGW Makefiles,
- NMake Makefiles,
- NMake Makefiles JOM,
- Unix Makefiles,
- Watcom WMake,
- Ninja,
- Visual Studio 6,
- Visual Studio 7,
- Visual Studio 7 .NET 2003,
- Visual Studio 8 2005,
- Visual Studio 9 2008,
- Visual Studio 10 2010,
- Visual Studio 11 2012,
- Visual Studio 12 2013,
- Visual Studio 14 2015,
- Visual Studio 15 2017,
- Visual Studio 16 2019,
- Green Hills MULTI,
- Xcode,
- CodeBlocks,
- CodeLite,
- Eclipse CDT4,
- Kate,
- Sublime Text 2.

Only by using different command line option you can target either MacOS XCode or Windows Visual Studio. Quite
impressive, wouldn’t you say?

3. CMake supports native shell commands/apps execution Despite being OS-independent, CMake still gives you ability to
execute custom host-specific shell commands or launch given application with the following commands:

- `execute_process()`,
- `add_custom_command()`.

However, this is not a good practice because it makes our build system tightly coupled with the concrete platform (which
is in contrary to the purpose of CMake).

## 4. CMake allows easy external project download and incorporation

In some cases we are forced to use some external projects from the remote location (e.g. Internet) or simply from
another local repository/disk directory. CMake has two integrated mechanisms for supporting that:

- `FetchContent()`,
- `ExternalProject_Add()`.
 
Both commands are almost identical except for one crucial difference: `FetchContent` is launched during the generation
time (when you call cmake) and `ExternalProject_Add` is launched during build time (e.g. when you call make).

Its usage is straightforward – you have to specify Git/SVN/file/other location and optional parameters (e.g. repository
branch) and CMake will automatically download and optionally build that project for you.

Here you have an example of downloading `libfmt` project from GitHub using `v11.0.2` tag:

```cmake linenums="1"
include(FetchContent)
FetchContent_Declare(fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG        v11.0.2
    SYSTEM
)

FetchContent_MakeAvailable(fmt)
```

After that, you have `libfmt` downloaded in your build directory and added to the project. Now you can treat that it
like normal source path (in particular link with any targets defined by `libfmt` repo).

## 5. CMake supports cross-compilation like a champ

Cross-compilation (building for platform other than you use for compilation) has always scared me. A task nearly
impossible to do manually in a cross-platform manner.

CMake has this ability built-in and requires very little effort to make it work for you. All you need to do is to
provide the so called toolchain file. It is a normal CMake file, except it doesn’t require its name to be
`CMakeLists.txt` (actually I would prefer it to be called `<toolchain_name>.cmake`). Below you can see an example
toolchain file for arm-none-eabi-gcc toolchain (`arm-none-eabi-gcc.cmake`):

```cmake linenums="1"
set(CMAKE_SYSTEM_NAME               Generic)
set(CMAKE_SYSTEM_PROCESSOR          arm)

# Without that flag CMake is not able to pass test compilation check
set(CMAKE_TRY_COMPILE_TARGET_TYPE   STATIC_LIBRARY)

set(CMAKE_AR                        ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-ar)
set(CMAKE_ASM_COMPILER              ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-gcc)
set(CMAKE_C_COMPILER                ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER              ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-g++)
set(CMAKE_LINKER                    ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-ld)
set(CMAKE_OBJCOPY                   ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-objcopy CACHE INTERNAL "")
set(CMAKE_RANLIB                    ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-ranlib CACHE INTERNAL "")
set(CMAKE_SIZE                      ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-size CACHE INTERNAL "")
set(CMAKE_STRIP                     ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-strip CACHE INTERNAL "")
set(CMAKE_GCOV                      ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-gcov CACHE INTERNAL "")

set(COMMON_FLAGS                    "-Wno-psabi --specs=nosys.specs -fdata-sections -ffunction-sections -Wl,--gc-sections")
set(CMAKE_C_FLAGS                   "${COMMON_FLAGS} ${APP_C_FLAGS} " CACHE INTERNAL "")
set(CMAKE_CXX_FLAGS                 "${COMMON_FLAGS} -fno-exceptions ${APP_CXX_FLAGS}" CACHE INTERNAL "")

set(CMAKE_C_FLAGS_DEBUG             "-Os -g" CACHE INTERNAL "")
set(CMAKE_C_FLAGS_RELEASE           "-Os -DNDEBUG" CACHE INTERNAL "")
set(CMAKE_CXX_FLAGS_DEBUG           "${CMAKE_C_FLAGS_DEBUG}" CACHE INTERNAL "")
set(CMAKE_CXX_FLAGS_RELEASE         "${CMAKE_C_FLAGS_RELEASE}" CACHE INTERNAL "")

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```

As you can see, this file only sets paths to several tools from the toolchain and sets common compilation flags
(specific for that compiler).

In order to tell CMake to use this configuration you have to set the `CMAKE_TOOLCHAIN_FILE` variable before the call to
`project()` function. So you can either set it as a command line argument:

```bash
cmake <PATH_TO_SOURCES> -DCMAKE_TOOLCHAIN_FILE=<PATH_TO_TOOLCHAIN_FILE>
```

or as a normal variable in the root `CMakeLists.txt`:

```cmake linenums="1"
cmake_minimum_required(VERSION 3.15)

set(CMAKE_TOOLCHAIN_FILE <PATH_TO_TOOLCHAIN_FILE>)

project(<PROJECT_NAME> ...)

...
```

## 6. CMake makes it easy to handle include paths

Before CMake 3.x when you wanted to set the include paths for the current directory and everything below you had to
write:

```cmake
include_directories(<PATH_TO_INCLUDES>)
```

This is bad! Don’t do that unless you know what you are doing. This is an anti-pattern of software architecture. In
order to get the includes from another library you had to know its internal structure (to include the proper sets of
paths). And what if that library is changed? You have to adjust every time. Nightmare!

Wouldn’t it be nice if that library provided you with everything you need with one statement? Since modern CMake (3.x+)
it is possible! Library author can utilize the fact, that when you “link” with that library via `target_link_libraries`
(quite unfortunate name: [read this for a reason why][modern-cmake]) you “inherit” all its public properties. And the
include paths are the property of the library. They can set via `target_include_directories` function.

So in other words, the library sets its include paths as its “include” property and when you link with it you
automatically get them. No need to write anything manually. Also the internal structure of the library is completely
hidden:

=== ":octicons-file-code-16: `CMakeLists.txt` for library A"

    ```cmake
    add_library(A <LIBRARY_A_SOURCES>)

    target_include_directories(
        PUBLIC liba/include
    )
    ```

=== ":octicons-file-code-16: `CMakeLists.txt` for library B"

    ```cmake
    add_library(B <LIBRARY_B_SOURCES>)

    target_link_libraries(B
        PRIVATE A             # Here we automatically get the liba/include includes.
    )
    ```

!!! note

    `PUBLIC`, `PRIVATE` and `INTERFACE` specifiers are explained in [this][modern-cmake] article.

<!-- Links -->

[cmake-docs]: https://cmake.org/cmake/help/latest/index.html
[modern-cmake]: modern-cmake-is-like-inheritance.md
